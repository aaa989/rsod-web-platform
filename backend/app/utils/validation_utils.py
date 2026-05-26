#!/usr/bin/env python3
"""
数据验证子系统（适配RSOD数据集结构）
"""

from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

# 导入路径管理模块
from .paths import Paths


class CheckLevel(Enum):
    """检查结果级别"""
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CheckResult:
    """单个检查结果"""
    level: CheckLevel
    message: str
    check_name: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckContext:
    """检查上下文（适配你的数据目录）"""
    annotations_dir: Optional[Path] = Paths.rsod_annotations()
    images_dir: Optional[Path] = Paths.rsod_images()
    classes: List[str] = field(default_factory=lambda: ["aircraft", "oiltank", "overpass", "playground"])
    image_extensions: List[str] = field(default_factory=lambda: [".jpg", ".jpeg", ".png"])
    extra: Dict[str, Any] = field(default_factory=dict)


# 验证器注册表
_validators = {}


def register_validator(name):
    """验证器装饰器"""
    def decorator(func):
        _validators[name] = func
        func._validator_name = name
        return func
    return decorator


def list_validators():
    """列出所有已注册的验证器"""
    return list(_validators.keys())


def get_validator(name):
    """获取指定验证器"""
    return _validators.get(name)


def run_validators(context, validator_names=None):
    """运行验证器"""
    results = []
    names = validator_names if validator_names is not None else list_validators()

    for name in names:
        validator = get_validator(name)
        if validator:
            try:
                check_results = validator(context)
                for r in check_results:
                    if not r.check_name:
                        r.check_name = name
                results.extend(check_results)
            except Exception as e:
                results.append(CheckResult(
                    level=CheckLevel.ERROR,
                    message=f"验证器执行失败: {str(e)}",
                    check_name=name
                ))

    return results


# ========== 内置验证器（适配你的数据） ==========
@register_validator("directories_exist")
def check_directories(ctx):
    """检查标注/图片目录是否存在"""
    results = []

    # 检查标注目录
    if ctx.annotations_dir:
        if ctx.annotations_dir.exists():
            results.append(CheckResult(
                level=CheckLevel.PASS,
                message=f"标注目录存在: {ctx.annotations_dir}"
            ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"标注目录不存在: {ctx.annotations_dir}"
            ))

    # 检查图片目录
    if ctx.images_dir:
        if ctx.images_dir.exists():
            results.append(CheckResult(
                level=CheckLevel.PASS,
                message=f"图片目录存在: {ctx.images_dir}"
            ))
        else:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"图片目录不存在: {ctx.images_dir}"
            ))

    return results


@register_validator("annotation_files")
def check_annotation_files(ctx):
    """检查XML标注文件数量"""
    results = []

    if not ctx.annotations_dir or not ctx.annotations_dir.exists():
        return results

    xml_files = list(ctx.annotations_dir.glob("*.xml"))
    if len(xml_files) == 0:
        results.append(CheckResult(
            level=CheckLevel.ERROR,
            message="未找到任何 XML 标注文件"
        ))
    else:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"找到 {len(xml_files)} 个 XML 标注文件",
            details={"count": len(xml_files)}
        ))

    return results


@register_validator("image_annotation_match")
def check_image_annotation_match(ctx):
    """检查图片和标注文件是否匹配"""
    results = []

    if not ctx.annotations_dir or not ctx.images_dir:
        return results

    # 收集标注文件basename
    xml_files = {f.stem for f in ctx.annotations_dir.glob("*.xml")}
    # 收集图片文件basename
    image_files = set()
    for ext in ctx.image_extensions:
        image_files.update({f.stem for f in ctx.images_dir.glob(f"*{ext}")})

    # 有标注无图片
    missing_images = xml_files - image_files
    if missing_images:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_images)} 个标注文件缺少对应图片",
            details={"missing": list(missing_images)[:10]}
        ))

    # 有图片无标注
    missing_annotations = image_files - xml_files
    if missing_annotations:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"{len(missing_annotations)} 个图片缺少对应标注",
            details={"missing": list(missing_annotations)[:10]}
        ))

    # 完全匹配
    if not missing_images and not missing_annotations:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message=f"图片和标注文件完全匹配，共 {len(xml_files & image_files)} 对"
        ))

    return results


@register_validator("class_validation")
def check_classes(ctx):
    """检查标注中的类别是否有效"""
    results = []

    if not ctx.annotations_dir or not ctx.classes:
        return results

    classes_set = set(ctx.classes)
    found_classes = set()
    unknown_classes = set()
    invalid_files = []

    # 遍历所有XML文件（适配你的少量标注文件场景）
    for xml_file in list(ctx.annotations_dir.glob("*.xml")):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for obj in root.findall("object"):
                name_elem = obj.find("name")
                if name_elem is not None:
                    class_name = name_elem.text
                    found_classes.add(class_name)
                    if class_name not in classes_set:
                        unknown_classes.add(class_name)
        except Exception as e:
            invalid_files.append(f"{xml_file.name}: {str(e)}")

    # 报告发现的类别
    if found_classes:
        results.append(CheckResult(
            level=CheckLevel.INFO,
            message=f"数据集中发现的类别: {sorted(found_classes)}"
        ))

    # 报告未知类别
    if unknown_classes:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"发现未知类别: {sorted(unknown_classes)}"
        ))

    # 报告无效文件
    if invalid_files:
        results.append(CheckResult(
            level=CheckLevel.WARNING,
            message=f"无法解析的 XML 文件: {len(invalid_files)} 个",
            details={"invalid_files": invalid_files}
        ))

    # 验证通过
    if not unknown_classes and not invalid_files:
        results.append(CheckResult(
            level=CheckLevel.PASS,
            message="类别验证通过"
        ))

    return results


class DataValidator:
    """数据验证器主类"""
    def __init__(self, context=None):
        self.context = context or CheckContext()
        self.results = []

    def validate(self, validator_names=None):
        """执行验证"""
        self.results = run_validators(self.context, validator_names)
        return self.results

    def validate_and_report(self):
        """执行验证并打印报告"""
        self.validate()
        self.print_report()
        # 判断是否有ERROR级别结果
        has_error = any(r.level == CheckLevel.ERROR for r in self.results)
        return not has_error

    def print_report(self):
        """打印格式化验证报告"""
        print("\n" + "="*80)
        print("RSOD 数据集验证报告")
        print("="*80)

        for result in self.results:
            icon = {
                CheckLevel.PASS: "✅",
                CheckLevel.INFO: "ℹ️",
                CheckLevel.WARNING: "⚠️",
                CheckLevel.ERROR: "❌"
            }.get(result.level, "🔍")

            print(f"{icon} [{result.level.value.upper()}] {result.check_name}: {result.message}")
            if result.details:
                print(f"   详情: {result.details}")

        print("="*80 + "\n")