#!/usr/bin/env python3

import os
import sys
import xml.etree.ElementTree as ET
import shutil
import random
from pathlib import Path

# 导入统一工具类
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.utils.paths import Paths
from app.utils.validation_utils import DataValidator
from app.utils.logging_utils import setup_convert_logging

# 初始化路径
Paths.init_all_dirs()

# 配置日志
logger = setup_convert_logging()

# 初始化数据验证器
validator = DataValidator()

# ====================== 你的原始代码（保留完整功能）======================
# RSOD 数据集类别映射
CLASSES = ["aircraft", "oiltank", "overpass", "playground"]
CLASS_MAP = {cls: idx for idx, cls in enumerate(CLASSES)}


def convert_xml_to_yolo(xml_path, image_width, image_height):
    """将单个 XML 文件转换为 YOLO 格式"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    lines = []
    for obj in root.findall("object"):
        name = obj.find("name").text
        if name not in CLASS_MAP:
            logger.warning(f"未知类别 '{name}'，已跳过")
            continue

        class_id = CLASS_MAP[name]
        bbox = obj.find("bndbox")
        xmin = int(bbox.find("xmin").text)
        ymin = int(bbox.find("ymin").text)
        xmax = int(bbox.find("xmax").text)
        ymax = int(bbox.find("ymax").text)

        # 归一化坐标
        x_center = (xmin + xmax) / 2.0 / image_width
        y_center = (ymin + ymax) / 2.0 / image_height
        bbox_width = (xmax - xmin) / image_width
        bbox_height = (ymax - ymin) / image_height

        lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")

    return "\n".join(lines)


def create_yaml_config(output_dir):
    """创建 YOLO 数据集配置文件"""
    yaml_content = f"""# RSOD 数据集配置文件
path: {output_dir}

train: images/train
val: images/val

nc: {len(CLASSES)}
names: {CLASSES}
"""
    yaml_path = output_dir / "rsod.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    logger.info(f"配置文件已创建：{yaml_path}")

# ====================== 优化后的转换器类 ======================
class RSODConverter:
    def __init__(self, split_ratio=0.8, seed=42):
        self.split_ratio = split_ratio
        self.seed = seed

        # 使用统一路径管理（适配你的目录）
        self.rsod_dir = Paths.rsod_data()
        self.annotations_dir = Paths.rsod_annotations()
        self.images_dir = Paths.rsod_images()
        self.output_dir = Paths.rsod_data() / "yolo_dataset"

        # 输出子目录
        self.train_images_dir = self.output_dir / "images" / "train"
        self.val_images_dir = self.output_dir / "images" / "val"
        self.train_labels_dir = self.output_dir / "labels" / "train"
        self.val_labels_dir = self.output_dir / "labels" / "val"

        # 自动创建目录
        self._create_dirs()

    def _create_dirs(self):
        """创建所有输出目录"""
        dirs = [
            self.train_images_dir, self.val_images_dir,
            self.train_labels_dir, self.val_labels_dir
        ]
        for d in dirs:
            Paths.ensure_dir(d)

    def validate_data(self):
        """数据验证"""
        logger.info("开始数据验证...")
        passed = validator.validate_and_report()
        if not passed:
            logger.error("数据验证失败，终止转换")
            sys.exit(1)
        logger.info("数据验证通过 ✅")

    def _process_file(self, filename, target_image_dir, target_label_dir):
        """处理单个文件（复制图片 + 生成标签）"""
        basename = os.path.splitext(filename)[0]

        # 复制图片
        src_image = self.images_dir / filename
        dst_image = target_image_dir / filename
        shutil.copy(src_image, dst_image)

        # 转换标注
        xml_path = self.annotations_dir / f"{basename}.xml"
        if xml_path.exists():
            # 你原来的尺寸：1024x768
            label_content = convert_xml_to_yolo(xml_path, 1024, 768)
            with open(target_label_dir / f"{basename}.txt", "w") as f:
                f.write(label_content)

    def convert_dataset(self):
        """执行数据集转换 + 划分"""
        # 获取所有图片
        image_files = [f for f in os.listdir(self.images_dir) if f.endswith(".jpg")]
        if not image_files:
            logger.error("未找到任何图片文件！")
            sys.exit(1)

        # 随机打乱
        random.seed(self.seed)
        random.shuffle(image_files)

        # 分割
        split_idx = int(len(image_files) * self.split_ratio)
        train_files = image_files[:split_idx]
        val_files = image_files[split_idx:]

        logger.info(f"训练集：{len(train_files)} 张 | 验证集：{len(val_files)} 张")

        # 处理训练集
        logger.info("开始处理训练集...")
        for f in train_files:
            self._process_file(f, self.train_images_dir, self.train_labels_dir)

        # 处理验证集
        logger.info("开始处理验证集...")
        for f in val_files:
            self._process_file(f, self.val_images_dir, self.val_labels_dir)

        # 生成配置文件
        create_yaml_config(self.output_dir)
        logger.info("数据集转换完成 ✅")

    def run(self):
        """运行完整流程"""
        try:
            logger.info("=" * 60)
            logger.info("RSOD → YOLO 数据集转换开始")
            logger.info(f"根目录：{Paths.root()}")
            logger.info(f"图片目录：{self.images_dir}")
            logger.info(f"输出目录：{self.output_dir}")

            # 1. 验证
            self.validate_data()

            # 2. 转换
            self.convert_dataset()

            logger.info("🎉 所有任务完成！")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"转换失败：{str(e)}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    converter = RSODConverter(split_ratio=0.8, seed=42)
    converter.run()