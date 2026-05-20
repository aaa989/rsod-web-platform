import os
import xml.etree.ElementTree as ET
import shutil
import random

# RSOD 数据集类别映射
CLASSES = ["aircraft", "oiltank", "overpass", "playground"]
CLASS_MAP = {cls: idx for idx, cls in enumerate(CLASSES)}


def convert_xml_to_yolo(xml_path, image_width, image_height):
    """
    将单个 XML 文件转换为 YOLO 格式

    参数：
        xml_path: XML 文件路径
        image_width: 图片宽度
        image_height: 图片高度

    返回：
        str: YOLO 格式的标注内容
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    lines = []
    for obj in root.findall("object"):
        # 获取类别名称
        name = obj.find("name").text
        if name not in CLASS_MAP:
            print(f"警告：未知类别 '{name}'，已跳过")
            continue

        # 获取类别 ID
        class_id = CLASS_MAP[name]

        # 获取边界框坐标
        bbox = obj.find("bndbox")
        xmin = int(bbox.find("xmin").text)
        ymin = int(bbox.find("ymin").text)
        xmax = int(bbox.find("xmax").text)
        ymax = int(bbox.find("ymax").text)

        # 转换为 YOLO 格式（归一化）
        x_center = (xmin + xmax) / 2.0 / image_width
        y_center = (ymin + ymax) / 2.0 / image_height
        bbox_width = (xmax - xmin) / image_width
        bbox_height = (ymax - ymin) / image_height

        # 格式化输出（类别ID 中心点X 中心点Y 宽度 高度）
        lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")

    return "\n".join(lines)


def convert_dataset(base_dir, split_ratio=0.8, seed=42):
    """
    转换整个数据集

    参数：
        base_dir: 数据集基础目录
        split_ratio: 训练集占比
        seed: 随机种子
    """
    # 路径配置
    rsod_dir = os.path.join(base_dir, "data", "rsod")
    images_dir = os.path.join(rsod_dir, "images")
    annotations_dir = os.path.join(rsod_dir, "annotations")

    # 输出目录
    output_dir = os.path.join(rsod_dir, "yolo_dataset")
    train_images_dir = os.path.join(output_dir, "images", "train")
    val_images_dir = os.path.join(output_dir, "images", "val")
    train_labels_dir = os.path.join(output_dir, "labels", "train")
    val_labels_dir = os.path.join(output_dir, "labels", "val")

    # 创建输出目录
    os.makedirs(train_images_dir, exist_ok=True)
    os.makedirs(val_images_dir, exist_ok=True)
    os.makedirs(train_labels_dir, exist_ok=True)
    os.makedirs(val_labels_dir, exist_ok=True)

    # 获取所有图片文件
    image_files = [f for f in os.listdir(images_dir) if f.endswith(".jpg")]

    # 随机打乱并分割
    random.seed(seed)
    random.shuffle(image_files)

    split_idx = int(len(image_files) * split_ratio)
    train_files = image_files[:split_idx]
    val_files = image_files[split_idx:]

    print(f"数据集分割完成：训练集 {len(train_files)} 张，验证集 {len(val_files)} 张")

    # 处理训练集
    for filename in train_files:
        # 获取图片名称（不含扩展名）
        basename = os.path.splitext(filename)[0]

        # 复制图片
        src_image = os.path.join(images_dir, filename)
        dst_image = os.path.join(train_images_dir, filename)
        shutil.copy(src_image, dst_image)

        # 转换标注
        xml_path = os.path.join(annotations_dir, f"{basename}.xml")
        if os.path.exists(xml_path):
            # 获取图片尺寸（这里简化处理，实际应读取图片）
            label_content = convert_xml_to_yolo(xml_path, 1024, 768)

            # 保存标注文件
            with open(os.path.join(train_labels_dir, f"{basename}.txt"), "w") as f:
                f.write(label_content)

    # 处理验证集（同上）
    for filename in val_files:
        basename = os.path.splitext(filename)[0]

        src_image = os.path.join(images_dir, filename)
        dst_image = os.path.join(val_images_dir, filename)
        shutil.copy(src_image, dst_image)

        xml_path = os.path.join(annotations_dir, f"{basename}.xml")
        if os.path.exists(xml_path):
            label_content = convert_xml_to_yolo(xml_path, 1024, 768)
            with open(os.path.join(val_labels_dir, f"{basename}.txt"), "w") as f:
                f.write(label_content)

    print(f"数据集转换完成！输出目录：{output_dir}")

    # 创建数据集配置文件
    create_yaml_config(output_dir)


def create_yaml_config(output_dir):
    """创建 YOLO 数据集配置文件"""
    yaml_content = f"""# RSOD 数据集配置文件
path: {output_dir}

train: images/train
val: images/val

nc: {len(CLASSES)}
names: {CLASSES}
"""

    with open(os.path.join(output_dir, "rsod.yaml"), "w") as f:
        f.write(yaml_content)

    print(f"配置文件已创建：{os.path.join(output_dir, 'rsod.yaml')}")


if __name__ == "__main__":
    # 执行转换（假设脚本在 backend 目录）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    convert_dataset(base_dir)