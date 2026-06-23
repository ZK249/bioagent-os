import logging
import sys
from pathlib import Path
from datetime import datetime

# 确保日志目录存在
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """统一结构化日志"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 控制台
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s")
    console.setFormatter(fmt)
    logger.addHandler(console)
    
    # 文件
    today = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(LOG_DIR / f"bioagent_{today}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    
    return logger