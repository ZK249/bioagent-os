import os
from typing import List, Dict
from ..llm_client import LLMClient


class RouterAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "router.txt"
        )

    def _load_prompt(self) -> str:
        if os.path.exists(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return """You are a query router. Classify the user query into one of:
- research: gene function, pathway, regulation, disease, protein, sequence analysis
- data: differential expression, clustering, visualization, scRNA-seq, bulk RNA-seq, statistics
- direct: general greeting, unclear, or simple factual questions

Respond with ONLY ONE word: research / data / direct"""

    def route(self, query: str) -> str:
        prompt = self._load_prompt()
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Query: {query}\n\nClassification:"}
        ]
        result = self.llm.generate(messages, max_tokens=10, temperature=0.0)
        result = result.strip().lower()
        if "data" in result:
            return "data"
        elif "research" in result:
            return "research"
        return "direct"