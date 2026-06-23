import time
from typing import List, Dict, Any
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, utility

from .base import BaseMemory


class LongTermMemory(BaseMemory):
    def __init__(self, collection_name: str = "agent_long_term", vectorizer=None, dense_dim: int = 768):
        self.collection_name = collection_name
        self.vectorizer = vectorizer
        self.dense_dim = dense_dim
        self._ensure_collection()

    def _ensure_collection(self):
        if not utility.has_collection(self.collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=self.dense_dim),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="memory_type", dtype=DataType.VARCHAR, max_length=32),
                FieldSchema(name="timestamp", dtype=DataType.INT64),
            ]
            schema = CollectionSchema(fields, description="Agent Long-term Memory")
            collection = Collection(self.collection_name, schema)
            collection.create_index(
                field_name="dense_vector",
                index_params={"index_type": "FLAT", "metric_type": "COSINE"}
            )
            collection.load()
        self.collection = Collection(self.collection_name)

    def add(self, key: str, value: Any, **kwargs) -> None:
        if self.vectorizer is None:
            return
        vectors = self.vectorizer.encode([str(value)], batch_size=1)
        
        entity_id = f"ltm_{int(time.time() * 1000)}"
        dense_vector = vectors["dense"][0]
        content = str(value)
        memory_type = key
        timestamp = int(time.time())
        
        # Milvus 2.4.x 插入格式：每个字段一个列表
        self.collection.insert([
            [entity_id],
            [dense_vector],
            [content],
            [memory_type],
            [timestamp],
        ])

    def get(self, key: str, **kwargs) -> Any:
        return None

    def search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        if self.vectorizer is None:
            return []
        vectors = self.vectorizer.encode([query], batch_size=1)
        results = self.collection.search(
            data=[vectors["dense"][0]],
            anns_field="dense_vector",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=top_k,
            output_fields=["content", "memory_type"]
        )
        hits = []
        for r in results[0]:
            hits.append({
                "content": r.content,
                "memory_type": r.memory_type,
                "distance": r.score
            })
        return hits

    def clear(self) -> None:
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)