from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.detection_service import detection_service
from app.config import settings

router = APIRouter(prefix="/model", tags=["model"])


class ModelItem(BaseModel):
    name: str
    version: str
    status: str


class ModelListResponse(BaseModel):
    success: bool
    message: str
    data: List[ModelItem]


class CurrentModelResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ModelItem]


class ReloadModelResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ModelItem]


@router.get("/list")
async def get_model_list():
    try:
        models = [
            {"name": "YOLO11", "version": "11.0", "status": "active"},
            {"name": "YOLO11n", "version": "11.0", "status": "available"},
        ]
        return {"success": True, "message": "获取成功", "data": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/current")
async def get_current_model():
    try:
        current_info = detection_service.current_model_info if hasattr(detection_service, 'current_model_info') else {}
        model_name = current_info.get('model_name', 'YOLO11')
        version = current_info.get('version', '11.0')
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "name": model_name,
                "version": version,
                "status": "loaded"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取当前模型失败: {str(e)}")


@router.post("/reload")
async def reload_model():
    try:
        if hasattr(detection_service, 'reload_model'):
            detection_service.reload_model()
        
        return {
            "success": True,
            "message": "模型重新加载成功",
            "data": {
                "name": "YOLO11",
                "version": "11.0",
                "status": "reloaded"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载模型失败: {str(e)}")
