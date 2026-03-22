from redis.asyncio import Redis
from redis.asyncio.client import Redis as RedisClient

from shared.config import get_settings

_redis: RedisClient | None = None


async def init_redis() -> None:
    global _redis
    settings = get_settings()
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> RedisClient:
    if _redis is None:
        raise RuntimeError("Redis has not been initialized. Call init_redis() first.")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
