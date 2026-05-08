from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from src.redis_service.init_redis import redis_client
from src.services.aiohttp_sessions.create_pull_sessions import http_client
from src.services.s3_storage.s3_service import s3_client
from src.rabbitmq_service.rabbitmq_client import rabbitmq_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await s3_client.init_client()
    await rabbitmq_client.init_connect()
    redis_client.init()
    http_client.init()

    yield
    
    await s3_client.close()
    await rabbitmq_client.close()
    await redis_client.close()
    await http_client.close()