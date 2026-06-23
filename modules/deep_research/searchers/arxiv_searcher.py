import requests
import xml.etree.ElementTree as ET
from typing import List
from .base import BaseSearcher, Paper
import time


class ArxivSearcher(BaseSearcher):
    """
    Arxiv API 检索（HTTP，无需额外包）
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        search_query = f"all:{query} AND cat:q-bio.*"
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        for attempt in range(3):
            try:
                r = requests.get(self.BASE_URL, params=params, timeout=60)
                r.raise_for_status()
                return self._parse_xml(r.text)
            except Exception as e:
                print(f"[Arxiv] Search attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    time.sleep(2)
                else:
                    print("[Arxiv] All retries failed, returning empty")
                    return []
        return []

    def _parse_xml(self, xml_text: str) -> List[Paper]:
        root = ET.fromstring(xml_text)
        # Arxiv Atom namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        papers = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            link = entry.find("atom:link[@type='application/pdf']", ns)
            id_url = entry.find("atom:id", ns)

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    authors.append(name.text)

            papers.append(Paper(
                title=title.text.strip() if title is not None else "Unknown",
                authors=authors,
                abstract=summary.text.strip() if summary is not None else "",
                year=published.text[:4] if published is not None else "",
                source="arxiv",
                url=id_url.text if id_url is not None else "",
                pdf_url=link.get("href") if link is not None else ""
            ))
        return papers