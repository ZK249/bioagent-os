from typing import Dict, Any, List
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .entity_memory import EntityMemory
from .working_memory import WorkingMemory


class MemoryManager:
    def __init__(self, vectorizer=None, redis_host: str = "localhost", redis_port: int = 6379):
        self.short_term = ShortTermMemory(host=redis_host, port=redis_port)
        self.long_term = LongTermMemory(vectorizer=vectorizer) if vectorizer else None
        self.entity = EntityMemory()
        self.working = WorkingMemory()

    def memorize_interaction(self, user_msg: str, assistant_msg: str, **kwargs):
        self.short_term.add("user", user_msg)
        self.short_term.add("assistant", assistant_msg)
        if self.long_term:
            self.long_term.add("interaction", f"User: {user_msg}\nAssistant: {assistant_msg}")

    def recall(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        return {
            "short_term": self.short_term.get(),
            "long_term": self.long_term.search(query, top_k) if self.long_term else [],
            "entities": self.entity.search(query, top_k),
            "working": self.working.state
        }

    def build_prompt_context(self, query: str) -> str:
        import json
        recall = self.recall(query)
        parts = []

        parts.append("## Working Memory\n" + self.working.to_prompt_context())

        history = recall["short_term"]
        if history:
            parts.append("## Recent Conversation\n")
            for h in history[-6:]:
                parts.append(f"{h['role']}: {h['content']}")

        if recall["long_term"]:
            parts.append("\n## Relevant Historical Knowledge\n")
            for r in recall["long_term"]:
                parts.append(f"- [{r['memory_type']}] {r['content'][:200]}... (score: {r['distance']:.3f})")

        if recall["entities"]:
            parts.append("\n## Known Entity Relations\n")
            for e in recall["entities"]:
                parts.append(f"- {e['head']} --[{e['relation']}]--> {e['tail']} (conf: {e['confidence']:.2f})")

        return "\n".join(parts)

    def clear_all(self):
        self.short_term.clear()
        if self.long_term:
            self.long_term.clear()
        self.entity.clear()
        self.working.clear()