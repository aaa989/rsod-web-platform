from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
import io
import uuid
import os
from typing import Optional
from app.config import settings

class MinIOService:

    def __init__(self):

        # 构建 MinIO 服务器地址，格式：主机:端口
        endpoint = f"{settings.minio.host}:{settings.minio.port}"

        # 创建 MinIO 客户端实例
        self.client = Minio(
            endpoint=endpoint,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            secure=settings.minio.secure                   # 是否使用 HTTPS
        )

        # 启动时确保所有需要的 Bucket 存在
        self._ensure_buckets()

    def _ensure_buckets(self):

        # 定义需要创建的 Bucket 列表
        buckets = [
            settings.minio.original_bucket,
            settings.minio.results_bucket,
            settings.minio.models_bucket
        ]

        # 遍历每个 Bucket，检查并创建
        for bucket in buckets:

            if not self.client.bucket_exists(bucket):
                try:
                    self.client.make_bucket(bucket)
                    print(f"Bucket '{bucket}' 创建成功")
                except S3Error as e:
                    print(f"创建 Bucket '{bucket}' 时出错: {e}")

            # 配置存储桶为公开读取
            self._set_bucket_public_read(bucket)
            print(f"存储桶 {bucket} 已配置为公开读取")

    def _set_bucket_public_read(self, bucket_name: str):

        # 定义公开读取的 Bucket Policy
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": f"PublicRead{bucket_name}",
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject", "s3:GetObjectVersion"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }

        try:
            import json
            policy_str = json.dumps(bucket_policy)
            self.client.set_bucket_policy(bucket_name, policy_str)
            print(f"存储桶 {bucket_name} 已设置为公开读取")
        except Exception as e:
            print(f"设置存储桶 {bucket_name} 公开读取失败: {str(e)}")

    def upload_image(self, file: UploadFile, bucket_name: str) -> str:

        # 从文件名中提取扩展名（如 jpg, png）,如果文件名没有扩展名，默认为 jpg
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"

        object_name = f"{uuid.uuid4().hex}.{file_extension}"

        file_content = file.file.read()

        file_bytes = io.BytesIO(file_content)

        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_bytes,
            length=len(file_content),
            content_type=file.content_type or "image/jpeg"
        )

        return object_name

    async def upload_image_async(self, file: UploadFile, bucket_name: str) -> str:

        # 从文件名中提取扩展名
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        object_name = f"{uuid.uuid4().hex}.{file_extension}"
        file_content = await file.read()
        file_bytes = io.BytesIO(file_content)

        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_bytes,
            length=len(file_content),
            content_type=file.content_type or "image/jpeg"
        )

        return object_name

    def upload_result_image(self, image_bytes: bytes, extension: str = "jpg") -> str:

        object_name = f"result_{uuid.uuid4().hex}.{extension}"

        file_bytes = io.BytesIO(image_bytes)

        self.client.put_object(
            bucket_name=settings.minio.results_bucket,
            object_name=object_name,
            data=file_bytes,
            length=len(image_bytes),
            content_type="image/jpeg"
        )

        return object_name

    def upload_image_bytes(self, image_bytes: bytes, original_filename: str) -> str:

        file_extension = original_filename.split(".")[-1] if "." in original_filename else "jpg"
        object_name = f"{uuid.uuid4().hex}.{file_extension}"
        file_bytes = io.BytesIO(image_bytes)
        content_type = f"image/{file_extension}" if file_extension in ["jpg", "jpeg", "png", "gif"] else "image/jpeg"

        self.client.put_object(
            bucket_name=settings.minio.original_bucket,
            object_name=object_name,
            data=file_bytes,
            length=len(image_bytes),
            content_type=content_type
        )
        
        return object_name

    def get_presigned_url(self, bucket_name: str, object_name: str, expires: int = 3600) -> Optional[str]:
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error:
            return None

    def get_public_url(self, bucket_name: str, object_name: str) -> str:

        return f"http://{settings.minio.host}:{settings.minio.port}/{bucket_name}/{object_name}"

    def delete_object(self, bucket_name: str, object_name: str) -> bool:

        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        except S3Error:
            return False

    def list_objects(self, bucket_name: str, prefix: str = "") -> list:

        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error:
            return []

    def bucket_exists(self, bucket_name: str) -> bool:
        return self.client.bucket_exists(bucket_name)


    def upload_model_file(self, local_file_path: str, model_name: str) -> str:
        file_extension = local_file_path.split(".")[-1] if "." in local_file_path else "pt"

        import time
        timestamp = int(time.time())
        object_name = f"{model_name}_{timestamp}.{file_extension}"

        with open(local_file_path, "rb") as f:
            file_content = f.read()

        file_bytes = io.BytesIO(file_content)

        self.client.put_object(
            bucket_name=settings.minio.models_bucket,
            object_name=object_name,
            data=file_bytes,
            length=len(file_content),
            content_type="application/octet-stream"
        )
        
        return object_name
    
    def download_model_file(self, object_name: str, local_save_path: str) -> bool:

        try:
            response = self.client.get_object(settings.minio.models_bucket, object_name)
            file_content = response.read()
            os.makedirs(os.path.dirname(local_save_path), exist_ok=True)
            with open(local_save_path, "wb") as f:
                f.write(file_content)
            
            return True
        except Exception as e:
            print(f"下载模型失败: {str(e)}")
            return False
    
    def list_models(self) -> list:
        return self.list_objects(settings.minio.models_bucket)
    
    def delete_model(self, object_name: str) -> bool:
        return self.delete_object(settings.minio.models_bucket, object_name)
    
    def get_latest_model(self, model_prefix: str = "rsod-yolo11n-best") -> Optional[str]:

        try:
            models = self.list_models()

            model_files = [
                m for m in models 
                if m.startswith(model_prefix) 
                and not m.endswith("_metadata.json")
                and m.endswith(".pt")
            ]
            
            if not model_files:
                return None

            def parse_model_name(filename: str):
                try:
                    if '_v' in filename:
                        parts = filename.split('_v')
                        if len(parts) >= 2:
                            rest = parts[1].split('_')
                            if len(rest) >= 2:
                                version_str = rest[0]
                                timestamp_part = rest[1].split('.')[0]
                                try:
                                    major, minor, patch = map(int, version_str.split('.'))
                                    return (1, major, minor, patch, int(timestamp_part))
                                except:
                                    pass

                    if '_' in filename and not '_v' in filename:
                        parts = filename.rsplit('_', 1)
                        if len(parts) >= 2:
                            timestamp_part = parts[1].split('.')[0]
                            if timestamp_part.isdigit():
                                return (0, 0, 0, 0, int(timestamp_part))
                
                except:
                    pass

                return (-1, 0, 0, 0, 0)

            model_files.sort(key=parse_model_name, reverse=True)
            return model_files[0]
            
        except Exception as e:
            print(f"获取最新模型失败: {str(e)}")
            return None
    
    def get_model_metadata(self, model_object_name: str) -> Optional[dict]:

        try:
            metadata_name = model_object_name.replace('.pt', '_metadata.json')

            response = self.client.get_object(settings.minio.models_bucket, metadata_name)
            metadata_content = response.read().decode('utf-8')
            
            import json
            return json.loads(metadata_content)
            
        except Exception as e:
            print(f"获取模型元数据失败: {str(e)}")
            return None
    
    def list_models_with_metadata(self, model_prefix: str = "rsod-yolo11n-best") -> list:

        try:
            models = self.list_models()

            model_files = [
                m for m in models 
                if m.startswith(model_prefix) 
                and not m.endswith("_metadata.json")
                and m.endswith(".pt")
            ]
            
            result = []
            for model_file in model_files:
                metadata = self.get_model_metadata(model_file)
                result.append({
                    "object_name": model_file,
                    "metadata": metadata,
                    "public_url": self.get_public_url(settings.minio.models_bucket, model_file)
                })
            
            return result
            
        except Exception as e:
            print(f"列出模型失败: {str(e)}")
            return []

minio_service = MinIOService()
