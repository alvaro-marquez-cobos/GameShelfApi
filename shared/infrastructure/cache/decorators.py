"""Caching decorator for async functions using Redis.

Provides a ``@cached`` decorator that transparently caches the JSON-serializable
return value of an async function in Redis with a configurable TTL. Cache
failures are logged and swallowed to ensure graceful degradation.
"""

import functools
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)


def cached(
    ttl: int,
    key_builder: Callable[..., str],
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    """Decorator that caches async function results in Redis.

    Args:
        ttl: Time-to-live in seconds for the cached value.
        key_builder: Callable that receives the same args as the decorated
            function and returns the Redis key string.
    """
    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from shared.infrastructure.cache.redis_client import get_redis

            key = key_builder(*args, **kwargs)
            try:
                redis = get_redis()
                cached_value = await redis.get(key)
                if cached_value is not None:
                    return json.loads(cached_value)
            except Exception:
                logger.warning("Cache read failed for key %s, proceeding without cache", key)

            result = await func(*args, **kwargs)

            try:
                redis = get_redis()
                await redis.setex(key, ttl, json.dumps(result))
            except Exception:
                logger.warning("Cache write failed for key %s", key)

            return result

        return wrapper

    return decorator
