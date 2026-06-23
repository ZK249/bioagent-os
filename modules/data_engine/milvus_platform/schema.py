from pymilvus import FieldSchema, DataType, CollectionSchema


class BioCollectionSchema:
    """
    将Milvus CollectionSchema定义为代码，便于版本管理和复用
    """

    @staticmethod
    def get_fields() -> list:
        fields = [
            # 主键
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=64,
                is_primary=True,
                description="全局唯一ID"
            ),
            # 双向量
            FieldSchema(
                name="dense_vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=1024,
                description="BGE-M3 dense embedding"
            ),
            FieldSchema(
                name="sparse_vector",
                dtype=DataType.SPARSE_FLOAT_VECTOR,
                description="BGE-M3 sparse lexical weights"
            ),
            # 内容字段
            FieldSchema(
                name="source_type",
                dtype=DataType.VARCHAR,
                max_length=32,
                description="数据来源：fasta/pdb/literature/expression"
            ),
            FieldSchema(
                name="doc_id",
                dtype=DataType.VARCHAR,
                max_length=128,
                description="原始文档ID"
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="文本内容（截断存储）"
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON,
                description="结构化元数据"
            ),
            # 生物领域标量（用于过滤和混合检索）
            FieldSchema(
                name="species",
                dtype=DataType.VARCHAR,
                max_length=64,
                nullable=True,
                description="物种"
            ),
            FieldSchema(
                name="seq_length",
                dtype=DataType.INT64,
                nullable=True,
                description="序列长度"
            ),
            FieldSchema(
                name="pdb_id",
                dtype=DataType.VARCHAR,
                max_length=32,
                nullable=True,
                description="PDB标识符"
            ),
            FieldSchema(
                name="chunk_idx",
                dtype=DataType.INT64,
                description="分块索引"
            ),
            # 时间戳（用于数据生命周期管理）
            FieldSchema(
                name="timestamp",
                dtype=DataType.INT64,
                description="摄入时间戳（Unix秒）"
            ),
        ]
        return fields

    @classmethod
    def get_schema(cls) -> CollectionSchema:
        return CollectionSchema(
            fields=cls.get_fields(),
            description="BioAgent-OS 多源生物知识库",
            enable_dynamic_field=True  # 允许动态字段，兼容未来扩展
        )