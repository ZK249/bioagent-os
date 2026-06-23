from typing import List, Dict, Optional
from pymilvus import AnnSearchRequest, RRFRanker
from modules.shared.logger import get_logger

logger = get_logger("HybridRetriever")


class HybridRetriever:
    def __init__(self, collection, weights: Dict[str, float]):
        self.collection = collection
        self.weights = weights

    def search(self,
               query_dense: List[float],
               query_sparse: Dict[int, float],
               top_k: int = 10,
               filters: Optional[str] = None,
               partition_names: Optional[List[str]] = None) -> List[Dict]:

        from modules.shared.logger import get_logger
        logger = get_logger("HybridRetriever")

        # 策略1：数据量预检查（可选，避免不必要的异常开销）
        try:
            total_entities = self.collection.num_entities
            if total_entities < 10:
                logger.info(f"Collection has only {total_entities} entities, "
                           f"using dense search directly to avoid hybrid_search inconsistency.")
                return self._dense_search(query_dense, top_k, filters, partition_names)
        except Exception:
            pass  # 如果 num_entities 拿不到，继续尝试 hybrid

        # 策略2：尝试 Hybrid Search，异常时降级 Dense Search
        try:
            dense_req = AnnSearchRequest(
                data=[query_dense],
                anns_field="dense_vector",
                param={"metric_type": "COSINE", "params": {"ef": 128}},
                limit=top_k * 2,
                expr=filters
            )

            sparse_req = AnnSearchRequest(
                data=[query_sparse],
                anns_field="sparse_vector",
                param={"metric_type": "IP", "params": {"drop_ratio_search": 0.2}},
                limit=top_k * 2,
                expr=filters
            )

            rerank = RRFRanker(k=60)

            results = self.collection.hybrid_search(
                reqs=[dense_req, sparse_req],
                rerank=rerank,
                limit=top_k,
                output_fields=["id", "content", "metadata", "source_type"],
                partition_names=partition_names
            )
            logger.info("Hybrid search executed successfully.")
            return self._format_results(results)

        except Exception as e:
            error_msg = str(e).lower()
            # 捕获 Milvus 的 inconsistent / incomplete / retry 异常
            if any(k in error_msg for k in ["inconsistent", "incomplete", "retry run out"]):
                logger.warning(f"Hybrid search failed (likely small dataset), "
                              f"falling back to dense search. Error: {e}")
                return self._dense_search(query_dense, top_k, filters, partition_names)
            else:
                # 其他异常不吞，继续抛
                raise

    def _dense_search(self, query_dense, top_k, filters, partition_names):
        """降级：纯 Dense 向量检索"""
        results = self.collection.search(
            data=[query_dense],
            anns_field="dense_vector",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=top_k,
            expr=filters,
            output_fields=["id", "content", "metadata", "source_type"],
            partition_names=partition_names
        )
        return self._format_results(results)

    def _format_results(self, results):
        """统一格式化输出（兼容 hybrid_search 和 search 的返回结构）"""
        hits = []
        for r in results[0]:
            hits.append({
                "id": r.id,
                "content": r.content,
                "source_type": r.source_type,
                "metadata": r.metadata,
                "distance": r.score  # search / hybrid_search 都用 .score
            })
        return hits

    def search_by_sequence(self,
                          seq: str,
                          vectorizer,
                          seq_type: str = "dna",
                          top_k: int = 5) -> List[Dict]:
        from ..preprocessors.sequence_processor import SequenceProcessor

        processor = SequenceProcessor(seq_type=seq_type)
        kmer_text = processor.kmer_tokenize(seq, k=6)
        vecs = vectorizer.encode([kmer_text])

        return self.search(
            query_dense=vecs['dense'][0],
            query_sparse=vecs['sparse'][0],
            top_k=top_k,
            filters=f"source_type == 'fasta'"
        )