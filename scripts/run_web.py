#!/usr/bin/env python3
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("BioAgent-OS Web 服务启动")
    print("=" * 60)
    print("地址: http://127.0.0.1:8000")
    print("按 Ctrl+C 停止")
    print("=" * 60)
    uvicorn.run("modules.agent_core.web.app:app", host="127.0.0.1", port=8000, reload=False)