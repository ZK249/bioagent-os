from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        pass