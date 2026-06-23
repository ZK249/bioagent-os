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

logger = get_logger("ingest_dnabert")


async def main():
    pipeline = BioIngestionPipeline("configs/data_engine_dnabert.yaml")
    pipeline.register_loader("fasta", FastaLoader)
    pipeline.register_loader("pdb", PDBLoader)

    real_dir = Path("data/real")

    # 1. 摄入真实 FASTA
    fasta_file = real_dir / "real_sequences.fasta"
    if fasta_file.exists():
        logger.info(">>> [DNABERT] Ingesting real FASTA...")
        result = await pipeline.process_stream(
            file_paths=[str(fasta_file)],
            source_type="fasta",
            species="Homo_sapiens"
        )
        logger.info(f"Real FASTA inserted: {result}")
    else:
        logger.warning("Real FASTA not found. Run: python scripts/download_real_data.py")

    # 2. 摄入真实 PDB
    pdb_files = sorted(real_dir.glob("pdb/*.pdb"))
    if pdb_files:
        logger.info(f">>> [DNABERT] Ingesting {len(pdb_files)} real PDB...")
        result = await pipeline.process_stream(
            file_paths=[str(f) for f in pdb_files],
            source_type="pdb"
        )
        logger.info(f"Real PDB inserted: {result}")

    # 3. 统计
    stats = pipeline.platform.get_partition_stats()
    total = sum(stats.values())
    logger.info(f"Total entities: {total}")

    # 4. 检索测试
    if total >= 3:
        logger.info(">>> [DNABERT] Testing search...")
        retriever = HybridRetriever(
            pipeline.platform.collection,
            weights={"dense": 0.5, "sparse": 0.5}
        )

        query = "CCTTACCTGGAGGGAGAATG"
        results = retriever.search_by_sequence(
            seq=query,
            vectorizer=pipeline.vectorizer,
            seq_type="dna",
            top_k=5
        )

        print("\n" + "=" * 60)
        print(f"[DNABERT] Query: {query}")
        print(f"Total DB entities: {total}")
        print("-" * 60)
        for r in results:
            print(f"  [{r['source_type']}] {r['id']} | score: {r['distance']:.4f}")
            print(f"    {r['content'][:100]}...")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())