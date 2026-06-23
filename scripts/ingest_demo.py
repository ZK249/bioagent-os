#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.data_engine.pipeline import BioIngestionPipeline
from modules.data_engine.loaders.fasta_loader import FastaLoader
from modules.data_engine.loaders.pdb_loader import PDBLoader
from modules.data_engine.milvus_platform.hybrid_retriever import HybridRetriever
from modules.shared.logger import get_logger

logger = get_logger("ingest_demo")

async def main():
    pipeline = BioIngestionPipeline("configs/data_engine.yaml")
    pipeline.register_loader("fasta", FastaLoader)
    pipeline.register_loader("pdb", PDBLoader)

    # 1. 摄入 FASTA（100 条）
    logger.info(">>> Ingesting FASTA...")
    result = await pipeline.process_stream(
        file_paths=["data/demo_sequences.fasta"],
        source_type="fasta",
        species="mixed_species"
    )
    logger.info(f"FASTA inserted: {result}")

    # 2. 摄入 PDB（10 个文件）
    logger.info(">>> Ingesting PDB...")
    pdb_files = [str(f) for f in Path("data").glob("demo_structure_*.pdb")]
    result = await pipeline.process_stream(
        file_paths=pdb_files,
        source_type="pdb"
    )
    logger.info(f"PDB inserted: {result}")

    # 3. 查看分区统计
    stats = pipeline.platform.get_partition_stats()
    logger.info(f"Partition stats: {stats}")
    total = sum(stats.values())
    logger.info(f"Total entities in collection: {total}")

    # 4. 混合检索测试
    logger.info(">>> Testing hybrid search...")
    retriever = HybridRetriever(
        pipeline.platform.collection,
        weights={"dense": 0.5, "sparse": 0.5}
    )

    query_seq = "TATAAAGCGATCGATCGATCGATCGATCG"
    results = retriever.search_by_sequence(
        seq=query_seq,
        vectorizer=pipeline.vectorizer,
        seq_type="dna",
        top_k=5
    )

    print("\n" + "=" * 60)
    print(f"Search results for query sequence (TATA box + random):")
    print(f"Total entities in DB: {total}")
    for r in results:
        print(f"  [{r['source_type']}] {r['id']} | score: {r['distance']:.4f}")
        print(f"    Content: {r['content'][:80]}...")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())