import time
import numpy as np
from ultralytics import YOLO
from app.config import settings  # 导入 config.py 中的 settings


class CameraDetectionService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.model = None
        self.class_names = {}
        self._load_model()
        self._init_class_names()

    def _load_model(self):
        # 直接用你现有的模型路径！
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        model_path = backend_dir / settings.YOLO_MODEL_PATH  # 你 config 里的路径

        if self.model is None:
            self.model = YOLO(model_path)

    def _init_class_names(self):
        # 和你原有 detection_service 保持完全一致
        self.class_names = {
            0: "person",
            1: "bicycle",
            2: "car",
            3: "motorcycle",
            4: "airplane",
            5: "bus",
        }

        # 中文名称（前端显示用）
        self.chinese_names = {
            "person": "人",
            "bicycle": "自行车",
            "car": "汽车",
            "motorcycle": "摩托车",
            "airplane": "飞机",
            "bus": "公交车",
        }

    def detect_image(self, image: np.ndarray):
        """摄像头帧检测（给前端用）"""
        start_time = time.time()

        # YOLO 推理（完全沿用你现有配置）
        results = self.model.predict(
            source=image,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            save=False,
            verbose=False
        )

        boxes = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.class_names.get(class_id, f"unknown")
                chinese_name = self.chinese_names.get(class_name, class_name)

                boxes.append({
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "confidence": confidence,
                    "class_id": class_id,
                    "class_name": class_name,
                    "chinese_name": chinese_name
                })

        detection_time = time.time() - start_time

        return {
            "boxes": boxes,
            "detection_time": detection_time,
            "total_objects": len(boxes)
        }


# 单例
camera_detection_service = CameraDetectionService()