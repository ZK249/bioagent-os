from typing import List, Dict
from .config import DeepResearchConfig
from .searchers.arxiv_searcher import ArxivSearcher
from .searchers.pubmed_searcher import PubMedSearcher
from .processors.paper_processor import PaperProcessor
from .synthesizers.review_generator import ReviewGenerator
from modules.agent_core.llm_client import LLMClient


class DeepResearchPipeline:
    """
    端到端 Deep Research Pipeline：
    检索 -> 处理 -> 存储 -> 综述
    """

    def __init__(self, llm_client: LLMClient, config_path: str = "configs/deep_research.yaml"):
        self.cfg = DeepResearchConfig(config_path)
        self.llm = llm_client
        self.arxiv = ArxivSearcher()
        self.pubmed = PubMedSearcher()
        self.processor = PaperProcessor()
        self.synthesizer = ReviewGenerator(llm_client)

    def run(self, query: str, sources: List[str] = None) -> Dict:
        if sources is None:
            sources = ["pubmed", "arxiv"]

        all_papers = []

        # PubMed（优先，国内稳定）
        if "pubmed" in sources:
            print(f"[DeepResearch] Searching PubMed: {query}")
            try:
                papers = self.pubmed.search(query, max_results=self.cfg.pubmed_max_results)
                print(f"   PubMed: {len(papers)} papers")
                all_papers.extend(papers)
            except Exception as e:
                print(f"   [PubMed] Failed: {e}")

        # Arxiv（超时降级，失败返回 0）
        if "arxiv" in sources:
            print(f"[DeepResearch] Searching Arxiv: {query}")
            try:
                papers = self.arxiv.search(query, max_results=self.cfg.arxiv_max_results)
                print(f"   Arxiv: {len(papers)} papers")
                all_papers.extend(papers)
            except Exception as e:
                print(f"   [Arxiv] Failed: {e}")

        # 处理
        unique = self.processor.deduplicate(all_papers)
        sorted_papers = self.processor.sort_by_year(unique)

        print(f"[DeepResearch] Total unique papers: {len(sorted_papers)}")

        # 生成综述（0 篇时 synthesizer 会处理）
        review = self.synthesizer.generate(query, sorted_papers[:10])

        return {
            "query": query,
            "papers": self.processor.to_dict_list(sorted_papers[:20]),
            "review": review,
            "total_papers": len(sorted_papers),
            "sources": sources
        }