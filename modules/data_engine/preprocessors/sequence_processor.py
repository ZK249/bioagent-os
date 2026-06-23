import re
from typing import List, Dict
import random

class SequenceProcessor:
    """FASTA序列预处理与标准化"""
    
    VALID_DNA = set("ATCGNatcgn")
    VALID_PROTEIN = set("ACDEFGHIKLMNPQRSTVWY")
    
    def __init__(self, seq_type: str = "dna"):
        self.seq_type = seq_type
    
    def clean(self, seq: str) -> str:
        """清洗非法字符，统一大写"""
        seq = seq.upper().strip()
        if self.seq_type == "dna":
            seq = "".join([c for c in seq if c in self.VALID_DNA])
            seq = seq.replace("N", "")  # 移除未知碱基
        return seq
    
    def chunk(self, seq: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict]:
        """滑动窗口分块（用于长序列向量化）"""
        chunks = []
        step = chunk_size - overlap
        for i in range(0, len(seq), step):
            chunk = seq[i:i+chunk_size]
            if len(chunk) < 100:  # 过滤过短片段
                continue
            chunks.append({
                "text": chunk,
                "start": i,
                "end": i + len(chunk),
                "chunk_type": "sequence"
            })
        return chunks
    
    def kmer_tokenize(self, seq: str, k: int = 6) -> str:
        """K-mer切分（复用GeneInsight经验，转为文本供BGE-M3编码）"""
        kmers = [seq[i:i+k] for i in range(len(seq)-k+1)]
        return " ".join(kmers)  # "ATCGAA TCGAAA ..."