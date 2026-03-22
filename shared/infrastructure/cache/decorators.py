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
