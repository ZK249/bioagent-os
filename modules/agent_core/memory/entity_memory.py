import time
from typing import List, Dict, Any
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, utility

from .base import BaseMemory


class EntityMemory(BaseMemory):
    def __init__(self, collection_name: str = "agent_entity_memory"):
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        if not utility.has_collection(self.collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="head", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="relation", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="tail", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="confidence", dtype=DataType.FLOAT),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="timestamp", dtype=DataType.INT64),
                # Milvus 本地文件模式要求至少一个 vector 字段
                FieldSchema(name="dummy_vector", dtype=DataType.FLOAT_VECTOR, dim=2),
            ]
            schema = CollectionSchema(fields, description="Agent Entity Memory")
            Collection(self.collection_name, schema)
            # 给 dummy_vector 建 FLAT 索引（本地模式要求）
            collection = Collection(self.collection_name)
            collection.create_index(
                field_name="dummy_vector",
                index_params={"index_type": "FLAT", "metric_type": "COSINE"}
            )
            collection.load()
        self.collection = Collection(self.collection_name)

    def add(self, key: str, value: Any, **kwargs) -> None:
        if not isinstance(value, dict):
            return
        
        entity_id = f"ent_{int(time.time() * 1000)}"
        head = value.get("head", "")
        relation = value.get("relation", "")
        tail = value.get("tail", "")
        confidence = value.get("confidence", 0.0)
        metadata = value.get("metadata", {})
        timestamp = int(time.time())
        dummy_vector = [0.0, 0.0]  # 占位
        
        # Milvus 2.4.x 插入格式：每个字段一个列表
        self.collection.insert([
            [entity_id],
            [head],
            [relation],
            [tail],
            [confidence],
            [metadata],
            [timestamp],
            [dummy_vector],
        ])

    def get(self, key: str, **kwargs) -> Any:
        return None

    def search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        expr = f'head == \"{query}\" or tail == \"{query}\"'
        results = self.collection.query(
            expr=expr,
            output_fields=["head", "relation", "tail", "confidence"],
            limit=top_k
        )
        return results

    def get_graph(self, entity: str, depth: int = 1) -> List[Dict]:
        return self.search(entity, top_k=20)

    def clear(self) -> None:
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)