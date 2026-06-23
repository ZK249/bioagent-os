from typing import Any, Dict
from .base import BaseTool
from modules.deep_research.pipeline import DeepResearchPipeline
from modules.agent_core.llm_client import LLMClient


class DeepResearchTool(BaseTool):
    """
    Deep Research 工具：Agent 调用文献检索 + 自动综述
    """

    def __init__(self, llm_client: LLMClient):
        self.pipeline = DeepResearchPipeline(llm_client)

    def name(self) -> str:
        return "deep_research"

    def description(self) -> str:
        return "Search scientific literature (Arxiv/PubMed) and generate a review"

    def run(self, query: str, sources: list = None, **kwargs) -> Dict[str, Any]:
        # 默认先查 PubMed，再查 Arxiv，Arxiv 超时自动降级
        result = self.pipeline.run(
            query, 
            sources=sources or ["pubmed", "arxiv"]
        )
        return {
            "tool": self.name(),
            "query": query,
            "papers_found": result["total_papers"],
            "review": result["review"],
            "top_papers": result["papers"][:5]
        }