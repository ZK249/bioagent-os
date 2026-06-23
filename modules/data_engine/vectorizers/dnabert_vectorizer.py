import os
import torch
import gc
from typing import List, Dict
from collections import Counter
from transformers import AutoTokenizer, AutoModel


class DNABERT_Vectorizer:
    """
    DNABERT-2 向量化器（117M参数，~468MB）
    接口与 BGE_M3_Vectorizer 完全兼容
    """

    def __init__(self, model_name: str = "zhihan1996/DNABERT-2-117M", device: str = "cpu"):
        model_name = os.path.expanduser(model_name)
        print(f"Loading DNABERT-2 from {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        self.model.to(device)
        self.model.eval()
        self.device = device
        self._dense_dim = 768
        print("DNABERT-2 loaded. Dense dim: 768")

    @property
    def dense_dim(self) -> int:
        return self._dense_dim

    def encode(self, texts: List[str], batch_size: int = 4) -> Dict[str, List]:
        all_dense = []
        all_sparse = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Pipeline 传入的是 K-mer 文本（带空格），还原为原始 DNA 序列
            clean_batch = [t.replace(" ", "") for t in batch]

            inputs = self.tokenizer(
                clean_batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Dense: [CLS] token embedding -> (batch_size, 768)
            embeddings = outputs[0][:, 0, :].cpu().numpy().tolist()
            all_dense.extend(embeddings)

            # Sparse: 基于 token frequency 构造合法 sparse 向量
            input_ids = inputs["input_ids"].cpu().numpy()
            pad_id = self.tokenizer.pad_token_id
            for seq in input_ids:
                # 过滤 padding token
                valid_ids = seq[seq != pad_id]
                freq = Counter(valid_ids)
                total = sum(freq.values())
                # 归一化频率作为 sparse 权重
                sparse_vec = {int(k): float(v / total) for k, v in freq.items()}
                all_sparse.append(sparse_vec)

            gc.collect()

        return {
            "dense": all_dense,
            "sparse": all_sparse
        }