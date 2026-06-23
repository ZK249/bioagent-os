from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Any, List
import aiofiles


@dataclass
class RawDocument:
    doc_id: str
    source_type: str
    raw_content: Any
    metadata: Dict[str, Any]
    file_path: str


class BaseLoader(ABC):
    def __init__(self, source_type: str):
        self.source_type = source_type

    @abstractmethod
    async def load(self, path: str, **kwargs) -> AsyncIterator[RawDocument]:
        pass

    async def load_batch(self, paths: List[str], **kwargs) -> AsyncIterator[RawDocument]:
        """顺序加载所有文件，产出全部文档流"""
        for path in paths:
            async for doc in self.load(path, **kwargs):
                yield doc