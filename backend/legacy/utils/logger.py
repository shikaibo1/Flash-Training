# utils/logger.py
import logging
import os

# 日志配置
LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOG_DIR, "shanlian_ai.log")
LOG_LEVEL = "INFO"

# 创建日志目录
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 初始化日志器
def init_logger(name: str = "shanlian_ai") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    if logger.handlers:
        return logger
    # 文件+控制台处理器
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

# 全局日志实例
logger = init_logger()