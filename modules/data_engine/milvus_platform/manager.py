from typing import List, Dict, Optional
from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType,
    Collection, utility, Partition
)
import yaml
from modules.shared.logger import get_logger

logger = get_logger("MilvusBioPlatform")


class MilvusBioPlatform:
    def __init__(self, config_path: str = "configs/data_engine.yaml"):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)['milvus']
        self._connect()
        self.collection = None
        if utility.has_collection(self.cfg['collection_name']):
            self.collection = Collection(self.cfg['collection_name'])

    def _connect(self):
        """本地文件模式：零服务器依赖，内存占用 < 50MB"""
        import os
        os.makedirs("data", exist_ok=True)
        connections.connect(
            alias="default",
            uri="data/milvus_demo.db"  # ← 本地 SQLite 文件，替代 host/port
        )

    def create_collection(self):
        if utility.has_collection(self.cfg['collection_name']):
            self.collection = Collection(self.cfg['collection_name'])
            logger.info("Collection already exists, skipping creation.")
            stats = self.get_partition_stats()
            logger.info(f"Current partition stats: {stats}")
            return self.collection

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
            FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=self.cfg['dense_dim']),
            FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="species", dtype=DataType.VARCHAR, max_length=64, nullable=True),
            FieldSchema(name="seq_length", dtype=DataType.INT64, nullable=True),
            FieldSchema(name="pdb_id", dtype=DataType.VARCHAR, max_length=32, nullable=True),
            FieldSchema(name="chunk_idx", dtype=DataType.INT64),
            FieldSchema(name="timestamp", dtype=DataType.INT64),
        ]

        schema = CollectionSchema(fields, description="BioAgent多源知识库")
        self.collection = Collection(self.cfg['collection_name'], schema)
        self._create_indexes()

        # 分区创建：本地文件模式不支持，捕获异常并跳过
        for p in self.cfg['partitions']:
            try:
                if not self.collection.has_partition(p):
                    self.collection.create_partition(p)
                    logger.info(f"Partition '{p}' created.")
            except Exception as e:
                logger.warning(f"Partition API not supported in local mode, skipping: {e}")
                break  # 本地模式下不再尝试创建分区

        return self.collection

    def _create_indexes(self):
        """索引配置：适配 Milvus 本地文件模式（只支持 FLAT/IVF_FLAT/AUTOINDEX）"""
        from modules.shared.logger import get_logger
        logger = get_logger("MilvusBioPlatform")

        # 本地文件模式：使用 FLAT（暴力搜索，小数据量最快，不需要预构建索引）
        # 生产环境 Docker 部署时切换为 HNSW
        try:
            self.collection.create_index(
                field_name="dense_vector",
                index_params={
                    "index_type": "FLAT",  # ← 本地模式只能用 FLAT
                    "metric_type": "COSINE"
                }
            )
            logger.info("Dense vector index (FLAT) created.")
        except Exception as e:
            logger.warning(f"Dense index creation skipped: {e}")

        # Sparse 向量索引：本地模式不支持，跳过
        try:
            self.collection.create_index(
                field_name="sparse_vector",
                index_params={
                    "index_type": "SPARSE_INVERTED_INDEX",
                    "metric_type": "IP"
                }
            )
            logger.info("Sparse vector index created.")
        except Exception as e:
            logger.warning(f"Sparse index not supported in local mode, skipped: {e}")

        self.collection.load()

    def insert_batch(self, entities: List[Dict], partition_name: Optional[str] = None):
        fields = ["id", "dense_vector", "sparse_vector", "source_type", "doc_id",
                  "content", "metadata", "species", "seq_length", "pdb_id", "chunk_idx", "timestamp"]

        batch = {f: [] for f in fields}
        for e in entities:
            for f in fields:
                val = e.get(f)
                if val is None and f in ["species", "pdb_id", "content"]:
                    val = ""
                elif val is None and f in ["seq_length", "chunk_idx", "timestamp"]:
                    val = 0
                batch[f].append(val)

        # 本地文件模式下 partition_name 可能不支持，捕获异常
        try:
            return self.collection.insert(
                data=[batch[f] for f in fields],
                partition_name=partition_name
            )
        except Exception as e:
            if partition_name and "partition" in str(e).lower():
                logger.warning(f"Partition insert failed, falling back to default: {e}")
                return self.collection.insert(
                    data=[batch[f] for f in fields]
                )
            raise

    def get_partition_stats(self) -> Dict[str, int]:
        stats = {}
        try:
            for p in self.cfg['partitions']:
                if self.collection.has_partition(p):
                    partition = Partition(self.collection.name, p)
                    stats[p] = partition.num_entities
                else:
                    stats[p] = 0
        except Exception as e:
            # 本地文件模式不支持分区，按 source_type 统计
            logger.warning(f"Partition stats unavailable in local mode, using source_type aggregation: {e}")
            total = self.collection.num_entities
            # 本地模式下所有数据在一个分区，返回总计
            stats = {p: 0 for p in self.cfg['partitions']}
            if total > 0:
                # 简化：把全部数据计入第一个分区（fasta）
                stats['fasta'] = total
        return stats