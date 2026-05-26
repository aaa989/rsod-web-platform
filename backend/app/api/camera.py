from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import base64
import cv2
import numpy as np
from app.services.camera_detection_service import camera_detection_service

router = APIRouter(prefix="/detection/camera", tags=["摄像头实时检测"])

# 接收前端传的 base64
class CameraFrameRequest(BaseModel):
    image: str

@router.post("/detect")
async def detect_camera_frame(req: CameraFrameRequest):
    try:
        image_data = req.image

        # 去掉 base64 前缀
        if "," in image_data:
            image_data = image_data.split(",")[1]

        # 解码
        image_bytes = base64.b64decode(image_data)
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if img is None:
            return {"success": False, "message": "图片解码失败"}

        # 调用检测
        result = camera_detection_service.detect_image(img)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        return {"success": False, "message": f"错误：{str(e)}"}