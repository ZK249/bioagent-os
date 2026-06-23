from typing import List, Dict
from .long_term import LongTermMemory
from .entity_memory import EntityMemory


class MemoryRetriever:
    def __init__(self, long_term: LongTermMemory, entity: EntityMemory):
        self.long_term = long_term
        self.entity = entity

    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, List[Dict]]:
        return {
            "long_term": self.long_term.search(query, top_k) if self.long_term else [],
            "entities": self.entity.search(query, top_k)
        }