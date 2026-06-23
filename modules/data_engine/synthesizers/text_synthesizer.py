import random
from typing import List, Dict
from modules.shared.llm_client import LLMClient  # 后续模块实现，这里先占位


class TextSynthesizer:
    """
    文献文本合成：摘要生成、问答对合成、反向翻译（用于数据增强）
    """

    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client
        self.prompts = {
            "summarize": "请用中文总结以下生物文献段落的核心发现，限制在100字以内：\n\n{text}",
            "qa_pair": "基于以下生物文献内容，生成3个高质量的问答对（Q&A），"
                      "问题应涉及机制、方法或应用，答案需准确且引用原文：\n\n{text}",
            "paraphrase": "请用学术英文改写以下段落，保持原意但改变句式结构：\n\n{text}"
        }

    def generate_summary(self, text: str) -> str:
        """生成摘要（可用于构建摘要向量索引）"""
        if not self.llm:
            # 无LLM时的降级策略：抽取前3句
            sentences = text.split(". ")[:3]
            return ". ".join(sentences) + "."
        
        prompt = self.prompts["summarize"].format(text=text[:3000])
        return self.llm.generate(prompt, max_tokens=200)

    def generate_qa_pairs(self, text: str, num_pairs: int = 3) -> List[Dict[str, str]]:
        """生成问答对（用于RAG训练数据/评估集）"""
        if not self.llm:
            return []
        
        prompt = self.prompts["qa_pair"].format(text=text[:3000])
        raw = self.llm.generate(prompt, max_tokens=800)
        
        # 简单解析 Q: ... A: ... 格式
        pairs = []
        segments = raw.split("Q:")
        for seg in segments[1:]:  # 跳过第一个空段
            if "A:" in seg:
                q, a = seg.split("A:", 1)
                pairs.append({
                    "question": q.strip(),
                    "answer": a.strip(),
                    "source_text": text[:500],
                    "synthesis_method": "llm_qa"
                })
        return pairs[:num_pairs]

    def paraphrase(self, text: str) -> str:
        """同义改写（用于数据增强，防止过拟合）"""
        if not self.llm:
            # 降级：句子重排
            sentences = text.split(". ")
            random.shuffle(sentences)
            return ". ".join(sentences)
        
        prompt = self.prompts["paraphrase"].format(text=text[:2000])
        return self.llm.generate(prompt, max_tokens=500)

    def synthetic_negative(self, positive_texts: List[str], num: int = 10) -> List[Dict]:
        """
        生成负样本：将正样本中的生物实体替换为无关实体
        用于训练RAG重排序器或分类器
        """
        # 简单的实体替换表
        replacements = {
            "protein": "metabolite",
            "gene": "pathway",
            "RNA": "lipid",
            "cell": "organism",
            "enzyme": "hormone"
        }
        
        negatives = []
        for _ in range(num):
            base = random.choice(positive_texts)
            neg_text = base
            for old, new in replacements.items():
                if old in neg_text.lower():
                    neg_text = neg_text.replace(old, new)
                    neg_text = neg_text.replace(old.capitalize(), new.capitalize())
            
            negatives.append({
                "text": neg_text,
                "label": 0,
                "synthesis_method": "entity_replacement"
            })
        
        return negatives