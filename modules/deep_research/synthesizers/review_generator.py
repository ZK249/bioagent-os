from typing import List
from modules.agent_core.llm_client import LLMClient
from ..searchers.base import Paper


class ReviewGenerator:
    """
    基于检索结果，调用 LLM 生成自动综述
    """

    SYSTEM_PROMPT = """You are an expert scientific literature reviewer. 
Your task is to synthesize the provided papers into a concise, structured review.
Include:
1. Research background and motivation
2. Key findings and methodologies
3. Gaps and limitations
4. Future directions

Be precise with biological terminology. Cite specific papers by number [1], [2], etc."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(self, query: str, papers: List[Paper]) -> str:
        if not papers:
            return "No relevant papers found for this query. Please try different keywords or check your network connection."

        # 格式化文献（只取真实存在的）
        lines = []
        for i, p in enumerate(papers, 1):
            authors = ', '.join(p.authors[:3]) if p.authors else 'Unknown'
            abstract = p.abstract[:400] if p.abstract else 'No abstract available'
            lines.append(f"[{i}] {p.title} ({p.year})")
            lines.append(f"    Authors: {authors}")
            lines.append(f"    Abstract: {abstract}")
            lines.append("")

        context = "\n".join(lines)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\nPapers:\n{context}\n\nPlease generate a structured literature review based on these papers."}
        ]

        return self.llm.generate(messages, max_tokens=3000, temperature=0.3)