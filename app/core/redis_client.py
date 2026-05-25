import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.redis = None

    async def connect(self):
        if not self.redis:
            self.redis = redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                max_connections=10
            )

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get_client(self):
        if not self.redis:
            await self.connect()
        return self.redis

redis_client = RedisClient()
