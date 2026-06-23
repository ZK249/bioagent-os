from abc import ABC, abstractmethod
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Paper:
    title: str
    authors: List[str]
    abstract: str
    year: str
    source: str          # arxiv / pubmed
    url: str
    pdf_url: str = ""
    citation_count: int = 0


class BaseSearcher(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        pass