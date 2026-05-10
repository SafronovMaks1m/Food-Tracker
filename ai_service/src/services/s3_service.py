from aiobotocore.session import get_session
from src.config import MINIO_USER, MINIO_PASSWORD, MINIO_CURRENT_INNER_URL
import aiofiles

class S3Client:    
    def __init__(self, access_key, secret_key, connect_url):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": connect_url
        }
        self.session = get_session()
        
    async def download_image(self, client, key: str, bucket: str):
        resp = await client.get_object(Bucket=bucket, Key=key)
        async with resp['Body'] as stream:
            data = await stream.read()
            return data
                    

s3_client = S3Client(
    access_key=MINIO_USER,
    secret_key=MINIO_PASSWORD,
    connect_url=MINIO_CURRENT_INNER_URL
)