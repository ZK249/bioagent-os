#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from modules.agent_core.llm_client import LLMClient
from modules.deep_research.pipeline import DeepResearchPipeline


def main():
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("KIMI_API_KEY")
    if not api_key:
        print("请设置 DEEPSEEK_API_KEY 或 KIMI_API_KEY")
        return

    print("=" * 60)
    print("BioAgent-OS 模块C：Deep Research 文献检索")
    print("=" * 60)

    # 初始化 LLM（复用模块B客户端）
    llm = LLMClient(
        provider="deepseek" if os.getenv("DEEPSEEK_API_KEY") else "kimi",
        api_key=api_key
    )

    # 初始化 Pipeline
    pipeline = DeepResearchPipeline(llm)

    # 测试查询
    query = "CRISPR gene editing in cancer immunotherapy"
    print(f"\nQuery: {query}")
    print("-" * 60)

    result = pipeline.run(query, sources=["arxiv", "pubmed"])

    print(f"\nTotal papers: {result['total_papers']}")
    print(f"Sources: {result['sources']}")
    print("\nTop Papers:")
    for i, p in enumerate(result['papers'][:5], 1):
        print(f"  {i}. [{p['year']}] {p['title'][:80]}...")
        print(f"     Source: {p['source']}")

    print("\n" + "=" * 60)
    print("Auto-Generated Review:")
    print("=" * 60)
    print(result['review'][:1500])
    print("...")

    print("\n" + "=" * 60)
    print("模块C 演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()