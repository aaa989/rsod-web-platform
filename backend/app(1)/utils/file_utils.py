import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config import settings

def ensure_directories():

    # 创建上传文件目录
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    # 创建检测结果文件目录
    Path(settings.RESULT_DIR).mkdir(parents=True, exist_ok=True)


def generate_unique_filename(original_filename: str) -> str:

    # 从原始文件名提取扩展名
    ext = Path(original_filename).suffix
    unique_name = f"temp_{uuid.uuid4().hex}{ext}"

    return unique_name
async def save_upload_file(file: UploadFile, upload_dir: str) -> str:

    filename = generate_unique_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return filename


def get_file_url(filename: str, directory: str) -> str:

    # 格式：http://localhost:8000/{directory}/{filename}
    return f"http://localhost:8000/{directory}/{filename}"
