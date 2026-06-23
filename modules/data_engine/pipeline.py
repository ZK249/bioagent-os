import asyncio
from typing import List, Dict, Type
from concurrent.futures import ThreadPoolExecutor
import time
import gc
import yaml
import importlib
from .loaders.base import BaseLoader, RawDocument
from .milvus_platform.manager import MilvusBioPlatform
from .preprocessors.sequence_processor import SequenceProcessor
from .preprocessors.structure_processor import StructureProcessor
from .preprocessors.text_processor import TextProcessor


class BioIngestionPipeline:
    """
    异步数据摄入流水线
    优化：降低 batch_size + 强制 gc.collect() 防止 OOM
    """
    def __init__(self, config_path: str = "configs/data_engine.yaml"):
        # 读取配置
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        
        self.platform = MilvusBioPlatform(config_path)
        
        # 动态加载 vectorizer（根据配置自动选择 BGE-M3 或 DNABERT）
        vec_cfg = self.cfg.get('vectorizer', {})
        vec_class_path = vec_cfg.get(
            'class', 
            'modules.data_engine.vectorizers.bge_m3_vectorizer.BGE_M3_Vectorizer'
        )
        module_path, class_name = vec_class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        vec_class = getattr(module, class_name)
        vec_params = vec_cfg.get('params', {})
        self.vectorizer = vec_class(**vec_params)
        
        self.executor = ThreadPoolExecutor(max_workers=2)  # 降低并发
        self.seq_processor = SequenceProcessor()
        self.struct_processor = StructureProcessor()
        self.text_processor = TextProcessor()
        self.loaders: Dict[str, Type[BaseLoader]] = {}

    def register_loader(self, source_type: str, loader_class: Type[BaseLoader]):
        self.loaders[source_type] = loader_class

    async def process_stream(self,
                            file_paths: List[str],
                            source_type: str,
                            **kwargs) -> Dict[str, int]:
        if source_type not in self.loaders:
            raise ValueError(f"No loader registered for {source_type}")

        loader = self.loaders[source_type]()
        total_inserted = 0
        raw_docs = []

        async for doc in loader.load_batch(file_paths, **kwargs):
            raw_docs.append(doc)
            if len(raw_docs) >= 5:  # 小批次：5 条一处理
                count = await self._process_batch(raw_docs, source_type)
                total_inserted += count
                raw_docs = []
                gc.collect()  # 强制释放 PyTorch 临时张量

        if raw_docs:
            count = await self._process_batch(raw_docs, source_type)
            total_inserted += count
            gc.collect()

        return {"inserted": total_inserted}

    async def _process_batch(self, docs: List[RawDocument], source_type: str) -> int:
        loop = asyncio.get_event_loop()
        processed = await loop.run_in_executor(
            self.executor,
            self._preprocess_sync,
            docs,
            source_type
        )

        texts = [p['text'] for p in processed]
        # batch_size=4 降低峰值内存
        vectors = self.vectorizer.encode(texts, batch_size=4)

        entities = []
        for i, p in enumerate(processed):
            entities.append({
                "id": p['doc_id'],
                "dense_vector": vectors['dense'][i],
                "sparse_vector": vectors['sparse'][i],
                "source_type": source_type,
                "doc_id": p['doc_id'],
                "content": p['text'],
                "metadata": p['metadata'],
                "species": p['metadata'].get('species', 'unknown'),
                "seq_length": p['metadata'].get('seq_length') or 0,
                "pdb_id": p['metadata'].get('pdb_id') or "",
                "chunk_idx": p['metadata'].get('chunk_idx', 0),
                "timestamp": int(time.time())
            })

        result = self.platform.insert_batch(entities, partition_name=source_type)
        return len(result.primary_keys)

    def _preprocess_sync(self, docs: List[RawDocument], source_type: str) -> List[Dict]:
        """同步预处理逻辑（在线程池中运行）"""
        processed = []

        for doc in docs:
            if source_type == "fasta":
                seq = self.seq_processor.clean(doc.raw_content)
                chunks = self.seq_processor.chunk(seq, chunk_size=512)
                for c in chunks:
                    processed.append({
                        "doc_id": f"{doc.doc_id}_c{c['start']}",
                        "text": self.seq_processor.kmer_tokenize(c['text'], k=6),
                        "metadata": {**doc.metadata, **c}
                    })

            elif source_type == "pdb":
                text = (
                    f"Protein structure {doc.metadata.get('pdb_id', '')} "
                    f"chain {doc.metadata.get('chain_id', '')} "
                    f"with {doc.metadata.get('num_residues', 0)} residues"
                )
                processed.append({
                    "doc_id": doc.doc_id,
                    "text": text,
                    "metadata": doc.metadata
                })

            elif source_type == "literature":
                text = doc.raw_content[:4000] if isinstance(doc.raw_content, str) else str(doc.raw_content)
                processed.append({
                    "doc_id": doc.doc_id,
                    "text": text,
                    "metadata": doc.metadata
                })

            elif source_type == "expression":
                text = ""
                if isinstance(doc.raw_content, dict):
                    text = doc.raw_content.get("text", "")
                else:
                    text = str(doc.raw_content)
                processed.append({
                    "doc_id": doc.doc_id,
                    "text": text,
                    "metadata": doc.metadata
                })

        return processed