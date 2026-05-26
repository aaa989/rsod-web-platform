import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # 把 backend 加入路径

import os
import time
import uuid
from datetime import datetime
from typing import List
from ultralytics import YOLO
import cv2

# 你原来的导入
from app.config import settings
from app.models.schemas import DetectionBox, DetectionResult
from app.utils.file_utils import get_file_url

# 工程优化：统一路径 + 日志
from app.utils.paths import Paths
from app.utils.logging_utils import setup_detection_logging

# 配置日志
logger = setup_detection_logging()


class DetectionService:
    def __init__(self):
        self.model = None
        self.class_names = {}

        # 修复目录创建（字符串也能兼容）
        result_dir = Path(settings.RESULT_DIR)
        Paths.ensure_dir(result_dir)

        self._load_model()
        self._init_class_names()
        logger.info("✅ 检测服务初始化完成")

    def _load_model(self):
        # ====================== 核心修改在这里 ======================
        # 自动定位到 backend 根目录
        backend_dir = Path(__file__).parent.parent.parent  # backend/
        model_path = backend_dir / "yolo11n.pt"  # backend/yolo11n.pt
        # ===========================================================

        logger.info(f"正在加载模型：{model_path}")

        if os.path.exists(model_path):
            self.model = YOLO(model_path)
            logger.info(f"✅ 模型加载成功")
        else:
            logger.error(f"❌ 模型文件不存在：{model_path}")
            raise FileNotFoundError(f"Model file not found: {model_path}")

    def _init_class_names(self):
        self.class_names = {
            0: "person",
            1: "bicycle",
            2: "car",
            3: "motorcycle",
            4: "airplane",
            5: "bus",
        }

    def detect_single_image(self, image_path: str, model_name: str = "pest-v1") -> DetectionResult:
        start_time = time.time()
        detection_id = str(uuid.uuid4())
        logger.info(f"开始检测：{os.path.basename(image_path)}")

        try:
            results = self.model.predict(
                source=image_path,
                conf=settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD,
                save=False
            )

            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.class_names.get(class_id, f"class_{class_id}")

                    boxes.append(DetectionBox(
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        confidence=confidence,
                        class_id=class_id, class_name=class_name
                    ))

            result_filename = f"result_{uuid.uuid4().hex}.jpg"
            result_path = os.path.join(settings.RESULT_DIR, result_filename)
            annotated_image = results[0].plot()
            cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

            detection_time = time.time() - start_time
            image_filename = os.path.basename(image_path)

            logger.info(f"检测完成 | 耗时：{detection_time:.3f}s | 目标数：{len(boxes)}")

            return DetectionResult(
                detection_id=detection_id,
                image_url=get_file_url(image_filename, "static/uploads"),
                result_image_url=get_file_url(result_filename, "static/results"),
                boxes=boxes,
                total_objects=len(boxes),
                detection_time=round(detection_time, 3),
                model_name=model_name,
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"检测失败：{str(e)}", exc_info=True)
            raise


# 初始化单例
detection_service = DetectionService()