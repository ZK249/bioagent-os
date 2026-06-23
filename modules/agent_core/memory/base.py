from abc import ABC, abstractmethod
from typing import Any, List, Dict


class BaseMemory(ABC):
    @abstractmethod
    def add(self, key: str, value: Any, **kwargs) -> None:
        pass

    @abstractmethod
    def get(self, key: str, **kwargs) -> Any:
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass