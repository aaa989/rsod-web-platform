#!/usr/bin/env python3
"""
统一日志管理模块（适配RSOD平台）
"""

import logging
import sys
from pathlib import Path
from .paths import Paths


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    level="INFO",
    log_file=None,
    log_dir=None,
    use_colors=True,
    name=None
):
    """统一日志配置函数"""
    # 日志格式（包含模块名，方便定位）
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 选择格式化器
    if use_colors and sys.stdout.isatty():
        formatter = ColoredFormatter(log_format, datefmt=date_format)
    else:
        formatter = logging.Formatter(log_format, datefmt=date_format)

    # 获取logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()  # 清除原有handler，避免重复输出

    # 添加控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 添加文件handler（如果指定）
    if log_file:
        log_path = Path(log_dir) if log_dir else Paths.root() / "logs"
        Paths.ensure_dir(log_path)
        log_file_path = log_path / log_file

        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        logger.addHandler(file_handler)

    return logger


# 预定义配置（适配你的场景）
def setup_production_logging():
    """生产环境日志配置"""
    return setup_logging(level="INFO", log_file="app.log")


def setup_debug_logging():
    """调试环境日志配置"""
    return setup_logging(level="DEBUG", log_file="debug.log")


def setup_convert_logging():
    """RSOD转换脚本专用日志配置"""
    return setup_logging(level="INFO", log_file="convert_rsod.log")


def setup_detection_logging():
    """检测服务专用日志配置"""
    return setup_logging(level="INFO", log_file="detection_service.log")