import re
from typing import List, Dict


class TextProcessor:
    """
    文献PDF/文本预处理：分句、去重、元数据抽取、去噪
    """

    # 常见的论文噪声模式
    NOISE_PATTERNS = [
        r"Downloaded from.*",
        r"All rights reserved.*",
        r"© \d{4}.*",
        r"https?://\S+",          # URL（可选保留）
        r"Figure \d+\..*",
        r"Table \d+\..*",
        r"^\s*\d+\s*$",           # 孤立页码
    ]

    def __init__(self):
        self.noise_regex = re.compile("|".join(self.NOISE_PATTERNS), re.IGNORECASE)

    def clean(self, text: str) -> str:
        """基础清洗：去噪声、统一空白"""
        # 去噪声行
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            if self.noise_regex.match(line.strip()):
                continue
            cleaned.append(line)
        text = "\n".join(cleaned)

        # 统一空白
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def split_sentences(self, text: str) -> List[str]:
        """分句（保留生物学术语中的小数点）"""
        # 保护常见缩写
        protected = text
        abbreviations = ["i.e.", "e.g.", "et al.", "Fig.", "Tab.", "Dr.", "Prof."]
        for abbr in abbreviations:
            protected = protected.replace(abbr, abbr.replace(".", "<DOT>"))

        # 分句
        sentences = re.split(r'(?<=[.!?])\s+', protected)
        sentences = [s.replace("<DOT>", ".") for s in sentences]
        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def chunk(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict]:
        """
        滑动窗口分块（按句子边界，避免截断语义）
        """
        sentences = self.split_sentences(text)
        chunks = []
        current = []
        current_len = 0

        for sent in sentences:
            sent_len = len(sent)
            if current_len + sent_len > chunk_size and current:
                # 保存当前块
                chunk_text = " ".join(current)
                chunks.append({
                    "text": chunk_text,
                    "length": len(chunk_text),
                    "num_sentences": len(current),
                    "chunk_type": "literature"
                })
                # 滑动窗口：保留overlap
                overlap_len = 0
                overlap_sents = []
                for s in reversed(current):
                    if overlap_len + len(s) > overlap:
                        break
                    overlap_sents.insert(0, s)
                    overlap_len += len(s)
                current = overlap_sents
                current_len = overlap_len

            current.append(sent)
            current_len += sent_len

        # 最后一个块
        if current:
            chunk_text = " ".join(current)
            chunks.append({
                "text": chunk_text,
                "length": len(chunk_text),
                "num_sentences": len(current),
                "chunk_type": "literature"
            })

        return chunks

    def extract_metadata(self, text: str) -> Dict[str, str]:
        """从文本头部抽取简单元数据（DOI/标题/作者，简化版）"""
        meta = {}
        # DOI
        doi_match = re.search(r"10\.\d{4,}/[^\s]+", text)
        if doi_match:
            meta["doi"] = doi_match.group(0)
        # 标题（假设为第一行非空且长度适中）
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:5]:
            if 20 < len(line) < 200 and not line.startswith("http"):
                meta["title"] = line
                break
        return meta