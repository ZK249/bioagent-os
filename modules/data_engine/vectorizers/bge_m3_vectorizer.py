from typing import List, Dict, Union
import torch
import gc
import numpy as np
from FlagEmbedding import BGEM3FlagModel  # BGE-M3官方包

class BGE_M3_Vectorizer:
    """
    BGE-M3同时产出：
    - Dense Embedding (1024d)
    - Sparse Embedding (词汇级权重，用于BM25语义)
    - ColBERT Token级向量（可选，用于重排序）
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        import os
        # 本地模型路径（相对于当前文件）
        local_path = os.path.join(
            os.path.dirname(__file__), 
            "../../../models/bge-m3"
        )
        local_path = os.path.abspath(local_path)
        
        if os.path.exists(os.path.join(local_path, "pytorch_model.bin")):
            print(f"Loading local model from {local_path}")
            model_path = local_path
        else:
            print(f"Local model not found, downloading from HuggingFace...")
            model_path = model_name
        
        self.model = BGEM3FlagModel(
            model_path,
            use_fp16=True if device == "cuda" else False,
            device=device
        )
        self._dense_dim = 1024

    
    def encode(self, texts: List[str], batch_size: int = 4) -> Dict[str, List]:      
        outputs = self.model.encode(
            texts,
            batch_size=batch_size,
            max_length=8192,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False
        )
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        sparse_vectors = []
        for lex_weights in outputs['lexical_weights']:
            sparse_vec = {int(k): float(v) for k, v in lex_weights.items()}
            sparse_vectors.append(sparse_vec)

        return {
            "dense": outputs['dense_vecs'].tolist(),
            "sparse": sparse_vectors
        }
    
    def encode_sequence(self, seq: str, k: int = 6) -> Dict[str, List]:
        """生物序列专用：先K-mer化再编码"""
        from ..preprocessors.sequence_processor import SequenceProcessor
        processor = SequenceProcessor()
        kmer_text = processor.kmer_tokenize(seq, k=k)
        return self.encode([kmer_text])