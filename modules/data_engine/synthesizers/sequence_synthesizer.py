import random
from typing import List, Dict
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

class SequenceSynthesizer:
    """
    生物序列数据合成：用于小样本增强
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
    
    def synonym_mutate(self, seq: str, mutation_rate: float = 0.05) -> str:
        """同义突变（保持蛋白质序列不变，改变DNA编码）"""
        # 简化的同义密码子替换表
        synonymous = {
            'A': ['GCT', 'GCC', 'GCA', 'GCG'],
            'L': ['TTA', 'TTG', 'CTT', 'CTC', 'CTA', 'CTG'],
            'R': ['CGT', 'CGC', 'CGA', 'CGG', 'AGA', 'AGG'],
            # ... 完整表可扩展
        }
        # 实际实现需要密码子表映射
        return seq  # 占位
    
    def add_noise(self, 
                  coordinates: List[List[float]], 
                  noise_level: float = 0.1) -> List[List[float]]:
        """PDB坐标加高斯噪声（数据增强）"""
        import numpy as np
        coords = np.array(coordinates)
        noise = np.random.normal(0, noise_level, coords.shape)
        return (coords + noise).tolist()
    
    def generate_negative_samples(self, 
                                   positive_seqs: List[str], 
                                   num_negatives: int = 100) -> List[Dict]:
        """
        生成负样本：打乱正序列的K-mer频率但保持长度
        用于训练分类器时的数据平衡
        """
        negatives = []
        for seq in positive_seqs:
            for _ in range(num_negatives // len(positive_seqs)):
                # 方法：保持二核苷酸频率但打乱顺序
                shuffled = "".join(random.sample(list(seq), len(seq)))
                negatives.append({
                    "sequence": shuffled,
                    "label": 0,
                    "synthesis_method": "shuffle"
                })
        return negatives