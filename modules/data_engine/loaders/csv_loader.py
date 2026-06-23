import aiofiles
import csv
from io import StringIO
from typing import AsyncIterator
import pandas as pd

from .base import BaseLoader, RawDocument


class CSVLoader(BaseLoader):
    """
    表达矩阵 / 单细胞 metadata / 临床数据加载器
    支持 CSV / TSV / MTX 等表格格式
    """

    def __init__(self):
        super().__init__("expression")

    async def load(self, path: str, **kwargs) -> AsyncIterator[RawDocument]:
        async with aiofiles.open(path, "r") as f:
            content = await f.read()

        # 用 pandas 解析，保留数值精度
        sep = kwargs.get("sep", ",")
        df = pd.read_csv(StringIO(content), sep=sep)

        # 按行拆分文档（每行是一个样本/细胞）
        id_col = kwargs.get("id_col", df.columns[0])
        text_cols = kwargs.get("text_cols", [])  # 需要文本向量化处理的列
        meta_cols = kwargs.get("meta_cols", [c for c in df.columns if c not in text_cols])

        for idx, row in df.iterrows():
            doc_id = f"{kwargs.get('dataset', 'csv')}_{row.get(id_col, idx)}"

            # 文本内容：将指定列拼接为描述文本
            text_parts = []
            for col in text_cols:
                if col in row and pd.notna(row[col]):
                    text_parts.append(f"{col}: {row[col]}")
            content_text = " | ".join(text_parts) if text_parts else ""

            metadata = {
                "total_rows": len(df),
                "columns": list(df.columns),
                **{k: row.get(k) for k in meta_cols if k in row and pd.notna(row[k])}
            }

            yield RawDocument(
                doc_id=doc_id,
                source_type="expression",
                raw_content={
                    "text": content_text,
                    "numeric_vector": row.select_dtypes(include=["number"]).values.tolist()
                },
                metadata=metadata,
                file_path=path
            )