import logging
import os
from datetime import datetime

def setup_logging():
    """
    配置应用程序的日志系统。
    日志将输出到控制台和文件。
    """
    # 获取根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # 设置最低日志级别

    # 避免重复添加处理器
    if not logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logging.info("日志系统已配置，日志将仅输出到控制台。")
