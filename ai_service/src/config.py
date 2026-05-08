import os
from dotenv import load_dotenv

load_dotenv()

MINIO_USER = os.getenv("MINIO_USER")
MINIO_PASSWORD = os.getenv("MINIO_PASSWORD")
MINIO_CURRENT_INNER_URL = os.getenv("MINIO_CURRENT_INNER_URL")
RABBITMQ_CONNECT_URL = os.getenv("RABBITMQ_CONNECT_URL")