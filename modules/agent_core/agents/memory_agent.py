from ..memory.memory_manager import MemoryManager
from ..llm_client import LLMClient


class MemoryAgent:
    def __init__(self, memory_manager: MemoryManager, llm_client: LLMClient):
        self.memory = memory_manager
        self.llm = llm_client

    def update(self, user_msg: str, assistant_msg: str):
        self.memory.memorize_interaction(user_msg, assistant_msg)