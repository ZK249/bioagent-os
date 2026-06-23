from typing import List, Dict
from pymilvus import Collection


class VectorStoreRAG:
    def __init__(self, collection: Collection):
        self.collection = collection

    def query(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        results = self.collection.search(
            data=[query_vector],
            anns_field="dense_vector",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=top_k,
            output_fields=["content", "source_type"]
        )
        hits = []
        for r in results[0]:
            hits.append({
                "content": r.content,
                "source_type": r.source_type,
                "distance": r.score
            })
        return hits