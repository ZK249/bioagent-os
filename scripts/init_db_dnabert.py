#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.data_engine.milvus_platform.manager import MilvusBioPlatform

if __name__ == "__main__":
    platform = MilvusBioPlatform("configs/data_engine_dnabert.yaml")
    platform.create_collection()
    print("DNABERT Database initialized successfully!")
    print(f"Collection: {platform.collection.name}")