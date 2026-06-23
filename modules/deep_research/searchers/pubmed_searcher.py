import requests
import time
from typing import List
from .base import BaseSearcher, Paper


class PubMedSearcher(BaseSearcher):
    """
    NCBI E-utilities API 检索
    esearch -> efetch -> 解析摘要
    """

    ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        # Step 1: esearch 获取 PMIDs
        try:
            r = requests.get(self.ESEARCH, params={
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": max_results,
                "sort": "relevance"
            }, timeout=30)
            r.raise_for_status()
            id_list = r.json().get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"[PubMed] esearch failed: {e}")
            return []

        if not id_list:
            return []

        # Step 2: efetch 获取详情（重试 3 次）
        papers = []
        for pmid in id_list:
            for attempt in range(3):
                try:
                    r = requests.get(self.EFETCH, params={
                        "db": "pubmed",
                        "id": pmid,
                        "retmode": "xml",
                        "rettype": "abstract"
                    }, timeout=60)  # 超时从 30 改 60
                    r.raise_for_status()
                    papers.extend(self._parse_xml(r.text))
                    time.sleep(0.5)  # 间隔从 0.3 改 0.5
                    break  # 成功，跳出重试
                except Exception as e:
                    print(f"[PubMed] efetch PMID {pmid} attempt {attempt+1}/3 failed: {e}")
                    if attempt < 2:
                        time.sleep(2)  # 失败后等 2 秒再试
                    else:
                        print(f"[PubMed] PMID {pmid} skipped after 3 retries")
        
        return papers

    def _parse_xml(self, xml_text: str) -> List[Paper]:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_text)
        papers = []

        for article in root.findall(".//PubmedArticle"):
            # 标题
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "Unknown"

            # 摘要
            abstract_elems = article.findall(".//AbstractText")
            abstract = " ".join([e.text for e in abstract_elems if e.text])

            # 作者
            authors = []
            for author in article.findall(".//Author"):
                last = author.find("LastName")
                first = author.find("ForeName")
                if last is not None:
                    name = last.text
                    if first is not None:
                        name = f"{first.text} {name}"
                    authors.append(name)

            # 年份
            year_elem = article.find(".//PubDate/Year")
            year = year_elem.text if year_elem is not None else ""

            # PMID -> URL
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            papers.append(Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                source="pubmed",
                url=url
            ))
        return papers