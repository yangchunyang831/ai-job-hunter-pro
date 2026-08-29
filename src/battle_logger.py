"""
Dedicated Live Testing & Battle Logger.
Outputs formatted, real-time logs to both console and `logs/live_battle.log`.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "live_battle.log"


class BattleLogger:
    """实战打靶与全链路风控实时日志系统"""
    
    _instance = None
    
    @classmethod
    def get_logger(cls):
        if cls._instance is None:
            cls._instance = cls._init_logger()
        return cls._instance
        
    @staticmethod
    def _init_logger():
        logger = logging.getLogger("BattleLogger")
        logger.setLevel(logging.DEBUG)
        
        if not logger.handlers:
            # 1. 文件输出 (UTF-8)
            file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
            file_handler.setLevel(logging.DEBUG)
            file_fmt = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(category)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_fmt)
            logger.addHandler(file_handler)
            
            # 2. 控制台输出
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_fmt = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(category)s] %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_fmt)
            logger.addHandler(console_handler)
            
        return logger

    @classmethod
    def log(cls, category: str, message: str, level: str = "INFO"):
        logger = cls.get_logger()
        extra = {"category": category.upper()}
        if level.upper() == "INFO":
            logger.info(message, extra=extra)
        elif level.upper() == "WARN" or level.upper() == "WARNING":
            logger.warning(message, extra=extra)
        elif level.upper() == "ERROR":
            logger.error(message, extra=extra)
        elif level.upper() == "ALERT":
            logger.critical(f"🚨 {message}", extra=extra)
        else:
            logger.debug(message, extra=extra)


# 便捷调用函数
def log_event(category: str, message: str, level: str = "INFO"):
    BattleLogger.log(category, message, level)
