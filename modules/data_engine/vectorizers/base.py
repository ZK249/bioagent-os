from abc import ABC, abstractmethod
from typing import List, Dict


class BaseVectorizer(ABC):
    """
    向量化器抽象基类：统一 Dense / Sparse / ColBERT 接口
    便于后续替换为其他模型（如E5、GTE）
    """

    @property
    @abstractmethod
    def dense_dim(self) -> int:
        """Dense向量维度"""
        pass

    @abstractmethod
    def encode(self, texts: List[str], batch_size: int = 32) -> Dict[str, List]:
        """
        批量编码
        Returns:
            {
                "dense": List[List[float]],      # (N, dense_dim)
                "sparse": List[Dict[int,float]],  # (N, {token_id: weight})
                "colbert": List[List[List[float]]] # (N, seq_len, dim) 可选
            }
        """
        pass

    @abstractmethod
    def encode_queries(self, texts: List[str], batch_size: int = 32) -> Dict[str, List]:
        """
        查询编码（部分模型对查询有特殊处理，如指令前缀）
        """
        pass