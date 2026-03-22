"""Redis connection lifecycle management.

Provides init, access, and teardown functions for the shared async Redis
connection used by caching and token blacklisting.
"""

from redis.asyncio import Redis
from redis.asyncio.client import Redis as RedisClient

from shared.config import get_settings

_redis: RedisClient | None = None


async def init_redis() -> None:
    """Initialize the global Redis connection from application settings."""
    global _redis
    settings = get_settings()
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> RedisClient:
    """Return the active Redis client, raising if not yet initialized."""
    if _redis is None:
        raise RuntimeError("Redis has not been initialized. Call init_redis() first.")
    return _redis


async def close_redis() -> None:
    """Gracefully close the Redis connection and reset the global reference."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
