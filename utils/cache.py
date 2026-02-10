import redis
from app.core.config import settings
from uuid import UUID


async def get_redis_client():
    return redis.Redis.from_url(settings.REDIS_URL)


async def invalidate_adventure_cache(adventure_id: UUID):
    redis = await get_redis_client()
    pattern = f"fastapi-cache:*adventure*{adventure_id}*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
    await redis.close()