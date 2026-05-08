from .RedisNotificationsException import RedisNotificationsException
from redis.asyncio import Redis

class RedisClient:
    def __init__(self):
        self.redis: Redis | None = None

    def init(self):
        self.redis = Redis(
            host="redis",
            port=6379,
            db=0,
            decode_responses=True
        )

    async def close(self):
        if self.redis:
            await self.redis.aclose()
    
    # async def publish(self, room_id: int, message: dict):
    #     message_json = json.dumps(message)
    #     await self.redis.publish(f"room:{room_id}", message_json)
        
redis_client = RedisClient()
