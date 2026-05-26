#!/usr/bin/env python3
"""
路径管理模块（适配当前backend目录结构）
统一管理项目所有路径，支持从任意子模块定位项目根目录
"""

from pathlib import Path
from typing import Optional
import inspect


def find_project_root(start_path=None, marker_file=".rsod_platform"):
    """从当前位置向上查找项目根目录（通过查找 marker file）"""
    if start_path is None:
        frame = inspect.stack()[1]
        start_path = Path(frame.filename).parent

    current = Path(start_path).resolve()

    for parent in [current] + list(current.parents):
        marker_path = parent / marker_file
        if marker_path.exists():
            return parent

    raise FileNotFoundError(
        f"Could not find {marker_file} in {current} or any parent directory"
    )


class Paths:
    """项目路径管理类（适配你的目录结构）"""
    _root = None
    _env = "development"

    @classmethod
    def root(cls):
        """获取项目根目录（backend/）"""
        if cls._root is None:
            cls._root = find_project_root()
        return cls._root

    @classmethod
    def app(cls):
        """主app目录: backend/app/"""
        return cls.root() / "app"

    @classmethod
    def app1(cls):
        """备用app目录: backend/app(1)/"""
        return cls.root() / "app(1)"

    @classmethod
    def data(cls):
        """数据根目录: backend/data/"""
        return cls.root() / "data"

    @classmethod
    def rsod_data(cls):
        """RSOD数据集根目录: backend/data/rsod/"""
        return cls.data() / "rsod"

    @classmethod
    def rsod_annotations(cls):
        """RSOD标注目录: backend/data/rsod/annotations/"""
        return cls.rsod_data() / "annotations"

    @classmethod
    def rsod_images(cls):
        """RSOD图片目录: backend/data/rsod/images/"""
        return cls.rsod_data() / "images"

    @classmethod
    def env_file(cls):
        """环境变量文件: backend/.env"""
        return cls.root() / ".env"

    @classmethod
    def ensure_dir(cls, path):
        """确保目录存在，不存在则创建"""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def init_all_dirs(cls):
        """初始化所有必要目录（首次运行时调用）"""
        dirs = [
            cls.data(),
            cls.rsod_data(),
            cls.rsod_annotations(),
            cls.rsod_images(),
            cls.root() / "logs"  # 新增日志目录
        ]
        for dir_path in dirs:
            cls.ensure_dir(dir_path)


# 便捷导出：常用路径
root = Paths.root()
data_dir = Paths.data()
rsod_annotations_dir = Paths.rsod_annotations()
rsod_images_dir = Paths.rsod_images()