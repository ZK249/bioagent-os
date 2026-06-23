import json
import redis
from typing import Any, List, Dict
from .base import BaseMemory


class ShortTermMemory(BaseMemory):
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, max_history: int = 10):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.max_history = max_history
        self.session_key = "session:current"

    def add(self, key: str, value: Any, **kwargs) -> None:
        msg = json.dumps({"role": key, "content": value, "timestamp": kwargs.get("timestamp", "")})
        self.client.lpush(self.session_key, msg)
        self.client.ltrim(self.session_key, 0, self.max_history * 2 - 1)

    def get(self, key: str = None, **kwargs) -> List[Dict]:
        raw = self.client.lrange(self.session_key, 0, -1)
        return [json.loads(r) for r in raw][::-1]

    def search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        return self.get()

    def clear(self) -> None:
        self.client.delete(self.session_key)

    def get_messages_for_llm(self) -> List[Dict]:
        history = self.get()
        return [{"role": h["role"], "content": h["content"]} for h in history]