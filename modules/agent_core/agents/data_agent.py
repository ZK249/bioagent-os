import os
from typing import Dict, Any
from ..memory.memory_manager import MemoryManager
from ..llm_client import LLMClient


class DataAgent:
    def __init__(self, memory_manager: MemoryManager, llm_client: LLMClient):
        self.memory = memory_manager
        self.llm = llm_client
        self.prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "bio_analysis.txt"
        )

    def _load_prompt(self) -> str:
        if os.path.exists(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return """You are a computational biology data analyst. Provide concrete code examples (Python/R), statistical rationale, and tool recommendations (Scanpy, Seurat, DESeq2). Flag batch effects."""

    def run(self, query: str, context: str) -> Dict[str, Any]:
        self.memory.working.add("task", f"DataAnalysis: {query}")
        self.memory.working.add("step", "pipeline_design")

        prompt = self._load_prompt()
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"}
        ]
        response = self.llm.generate(messages, max_tokens=2000)

        return {
            "agent": "DataAgent",
            "response": response,
            "tools_used": []
        }