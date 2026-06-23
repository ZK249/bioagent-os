import os
import re
from typing import Dict, Any
from ..memory.memory_manager import MemoryManager
from ..llm_client import LLMClient
from ..tools.search_tool import DeepResearchTool


class ResearchAgent:
    def __init__(self, memory_manager: MemoryManager, llm_client: LLMClient):
        self.memory = memory_manager
        self.llm = llm_client
        self.prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "bio_analysis.txt"
        )
        self.research_tool = DeepResearchTool(llm_client)

    def _load_prompt(self) -> str:
        if os.path.exists(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return """You are an expert bioinformatics researcher. Analyze the biological query with precision. Cite genes, pathways, and mechanisms. Suggest follow-up analyses."""

    def run(self, query: str, context: str) -> Dict[str, Any]:
        self.memory.working.add("task", f"Research: {query}")
        self.memory.working.add("step", "biological_analysis")

        # 检测是否需要文献检索
        research_keywords = ["literature", "paper", "review", "recent", "study", "research", "pubmed", "arxiv", "survey", "latest"]
        needs_research = any(k in query.lower() for k in research_keywords)

        tool_result = None
        # ========== 模块C 集成：文献检索 ==========
        if needs_research:
            self.memory.working.add("step", "literature_search")
            
            clean_query = self._extract_search_query(query)
            print(f"[ResearchAgent] Calling DeepResearch: {clean_query}")
            
            tool_result = self.research_tool.run(clean_query)
            papers_found = tool_result.get('papers_found', 0)
            print(f"[ResearchAgent] Found {papers_found} papers")

            # 关键：如果真实文献为 0，直接返回提示，不 hallucinate
            if papers_found == 0:
                return {
                    "agent": "ResearchAgent",
                    "response": "No relevant papers found. Please try different keywords or check your network connection.",
                    "tools_used": [tool_result]
                }

            # 基于真实文献让 LLM 写综述
            papers = tool_result.get('top_papers', [])
            paper_lines = []
            for i, p in enumerate(papers[:5], 1):
                authors = ', '.join(p.get('authors', [])[:3]) if p.get('authors') else 'Unknown'
                abstract = p.get('abstract', '')[:400]
                paper_lines.append(
                    f"[{i}] {p.get('title', 'Unknown')} ({p.get('year', 'N/A')})\n"
                    f"    Authors: {authors}\n"
                    f"    Abstract: {abstract}..."
                )
            
            literature_context = "\n\n".join(paper_lines)
            
            prompt = self._load_prompt()
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": 
                    f"I found {papers_found} relevant papers. "
                    f"Here are the top {len(papers[:5])} papers:\n\n"
                    f"{literature_context}\n\n"
                    f"Please write a comprehensive literature review based on these papers. "
                    f"Cite papers by number [1], [2], etc."}
            ]
            response = self.llm.generate(messages, max_tokens=3000)

            return {
                "agent": "ResearchAgent",
                "response": response,
                "tools_used": [tool_result]
            }

    def _extract_entities(self, text: str):
        genes = re.findall(r'\b([A-Z][A-Z0-9]{1,5})\b', text)
        for g in genes:
            if 2 <= len(g) <= 6:
                self.memory.entity.add("gene", {
                    "head": g,
                    "relation": "mentioned_in",
                    "tail": "research_analysis",
                    "confidence": 0.7
                })

    def _extract_search_query(self, query: str) -> str:
        """
        用 LLM 把自然语言转换为学术数据库检索关键词
        支持中英文混合输入
        """
        # 如果查询已经很短（< 30 字符），直接返回
        if len(query) < 30:
            return query
        
        prompt = """You are a search query optimizer for academic databases (PubMed, Arxiv).
            Your task: convert the user's natural language question into a concise keyword query (3-8 keywords) suitable for academic search.
            Rules:
            - Remove polite phrases, filler words, and questions
            - Keep gene names, protein names, diseases, techniques, and key biological terms
            - Output ONLY the keywords, no explanation, no punctuation except spaces
            - Support both English and Chinese input

            Examples:
            Input: "Please review recent literature on CRISPR gene editing in cancer immunotherapy"
            Output: CRISPR gene editing cancer immunotherapy

            Input: "请帮我查一下TP53在细胞周期调控中的相关文献"
            Output: TP53 cell cycle regulation

            Input: "What is the latest research on single-cell RNA sequencing in Alzheimer's disease?"
            Output: single-cell RNA sequencing Alzheimer's disease scRNA-seq"""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Input: {query}\nOutput:"}
        ]
        
        try:
            result = self.llm.generate(messages, max_tokens=100, temperature=0.0)
            clean = result.strip().replace('"', '').replace("'", "")
            print(f"[ResearchAgent] LLM extracted keywords: {clean}")
            return clean if len(clean) > 5 else query
        except Exception as e:
            print(f"[ResearchAgent] LLM keyword extraction failed: {e}, fallback to raw query")
            return query