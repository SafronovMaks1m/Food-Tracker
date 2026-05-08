from .init_redis import redis_client
from redis.asyncio import Redis

def get_redis_connection() -> Redis:
    return redis_client.redis