from typing import List
from ..searchers.base import Paper


class PaperProcessor:
    """
    文献结果处理：去重、排序、格式化
    """

    def deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """按标题去重"""
        seen = set()
        unique = []
        for p in papers:
            key = p.title.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique

    def sort_by_year(self, papers: List[Paper]) -> List[Paper]:
        """按年份降序"""
        return sorted(papers, key=lambda x: x.year, reverse=True)

    def format_for_prompt(self, papers: List[Paper], max_chars: int = 8000) -> str:
        """格式化为 LLM prompt"""
        lines = []
        total = 0
        for i, p in enumerate(papers, 1):
            entry = f"{i}. [{p.year}] {p.title}\\n   Authors: {', '.join(p.authors[:3])}\\n   Abstract: {p.abstract[:300]}...\\n   Source: {p.source}\\n\\n"
            if total + len(entry) > max_chars:
                break
            lines.append(entry)
            total += len(entry)
        return "".join(lines)

    def to_dict_list(self, papers: List[Paper]) -> List[dict]:
        """转为字典列表（用于 JSON 返回）"""
        return [
            {
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract[:500],
                "year": p.year,
                "source": p.source,
                "url": p.url
            }
            for p in papers
        ]