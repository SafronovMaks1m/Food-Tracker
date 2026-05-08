from redis.asyncio import Redis
from fastapi import status
from src.celery_service.bg_tasks import send_messages
from .verification_error import VerificationError
import secrets

class VerificationService:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    def generate_code(self):
        code = "".join([str(secrets.randbelow(10)) for i in range(6)])
        return code
    
    async def verification_code(self, code: str, name: str, email):
        limit_key = f"limit:{email}"
        total_limit_key = f"total_limit:{email}"
        
        if await self.redis.exists(name) == 0:
            raise VerificationError("Код просрочен или не существует")
        
        stored_code = await self.redis.hget(name, "code")
        
        if stored_code != code:
            new_attempts = await self.redis.hincrby(name, "attempts", 1)
            if new_attempts >= 5:
                await self.redis.delete(name)
                raise VerificationError("Слишком много попыток. Получите новый код")
        
            raise VerificationError("Неверный код")
        
        await self.redis.delete(total_limit_key, name, limit_key)
        return True
    
    async def get_code(self, prefix: str, email: str):
        name = f"{prefix}:{email}"
        limit_key = f"limit:{email}"
        total_limit_key = f"total_limit:{email}"
        ban_email = f"ban:{email}"
        
        if await self.redis.exists(ban_email):
            raise VerificationError("Пожалуйста попробуйте позже", status_code=429)
        
        if await self.redis.exists(limit_key):
            raise VerificationError("Подождите 60 секунд", status_code=429)
        
        if await self.redis.exists(total_limit_key) == 0:
            await self.redis.set(total_limit_key, 1, ex=3600)
        else:
            total = await self.redis.get(total_limit_key)
            if int(total) > 5:
                async with self.redis.pipeline() as pipe:
                    pipe.set(ban_email, "1", ex=1800)
                    pipe.delete(total_limit_key)
                    await pipe.execute()
                raise VerificationError("Пожалуйста попробуйте позже", status_code=429)
            await self.redis.incr(total_limit_key)
            
        code = self.generate_code()
        async with self.redis.pipeline() as pipe:
            pipe.hset(name, mapping={"code": code, "attempts": 0})
            pipe.expire(name, 600)
            pipe.set(limit_key, "active", ex=60)
            await pipe.execute()
        
        send_messages.delay(email, prefix, code)