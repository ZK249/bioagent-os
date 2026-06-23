#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.data_engine.milvus_platform.manager import MilvusBioPlatform
from modules.shared.logger import get_logger

logger = get_logger("init_db")

def init_milvus():
    logger.info(">>> Initializing Milvus...")
    platform = MilvusBioPlatform("configs/data_engine.yaml")
    platform.create_collection()
    stats = platform.get_partition_stats()
    logger.info(f"Milvus ready. Partitions: {stats}")

def main():
    init_milvus()
    print("=" * 50)
    print("Database initialized successfully!")

if __name__ == "__main__":
    main()