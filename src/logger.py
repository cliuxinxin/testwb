import logging
import os
from datetime import datetime


def setup_logger():
    # 确保日志目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志文件名按天生成
    log_file = os.path.join(
        log_dir, f"wq_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    # 创建全局 Logger
    logger = logging.getLogger("WQ_BOT")
    logger.setLevel(logging.DEBUG)  # 捕获 DEBUG 及以上所有级别日志

    # 避免重复添加 Handler
    if not logger.handlers:
        # 1. 终端输出 Handler (输出 INFO 及以上，格式简洁)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)

        # 2. 文件输出 Handler (输出 DEBUG 及以上，格式详尽)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s][%(filename)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# 实例化全局可用的 logger
logger = setup_logger()
