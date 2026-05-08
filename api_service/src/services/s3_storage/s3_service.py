from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status
from aiobotocore.client import AioBaseClient
from src.config import MINIO_USER, MINIO_PASSWORD, MINIO_CURRENT_INNER_URL
from uuid import uuid4
from loguru import logger
import json, filetype


class S3Client:
    
    ALLOWED_IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp")
    MAX_IMAGE_SIZE = 1024 * 1024 * 5
    BUCKETS = ("avatars", "food-images")
    
    def __init__(self, access_key, secret_key, connect_url):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": connect_url
        }
        self.session = get_session()
        self.client: AioBaseClient = None
    
    async def init_buckets(self):
        for bucket_name in self.BUCKETS:
            try:
                await self.client.head_bucket(Bucket=bucket_name)
            except ClientError as exp:
                error_code = exp.response['Error']['Code']
                if error_code == '404':
                    await self.client.create_bucket(Bucket=bucket_name)
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": ["*"]},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                            }
                        ]
                    }
                    await self.client.put_bucket_policy(
                        Bucket=bucket_name,
                        Policy=json.dumps(policy)
                    )
                else:
                    logger.critical(f"Ошибка при инициализации S3. Ошибка: {exp}")
                    raise exp
        
    async def init_client(self):
        self.client = await self.session.create_client("s3", **self.config).__aenter__()
        await self.init_buckets()
    
    async def check_image(self, file: UploadFile):
        header = await file.read(2048)
        kind = filetype.guess(header)
        
        if kind is None or kind.mime not in self.ALLOWED_IMAGE_TYPES:
            await file.seek(0)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат или неопознанный тип файла"
            )
        await file.seek(0)
        size = 0
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > self.MAX_IMAGE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE, 
                    detail="Размер файла слишком большой"
                )
        await file.seek(0)
        
        return {
            "mime": kind.mime,
            "extension": kind.extension
        }
    
    async def upload_image(self, bucket: str, image: UploadFile):
        data = await self.check_image(image)
        file_name = f"{uuid4().hex}.{data["extension"]}"
        await self.client.put_object(
            Bucket=bucket,
            Key=file_name,
            Body=image.file,
            ContentType=data["mime"]
        )
        return file_name
        
    async def delete_image(self, bucket: str, key: str): 
        await self.client.delete_object(Bucket=bucket, Key=key)
    
    async def close(self):
        await self.client.__aexit__(None, None, None)

s3_client = S3Client(
    access_key=MINIO_USER,
    secret_key=MINIO_PASSWORD,
    connect_url=MINIO_CURRENT_INNER_URL
)