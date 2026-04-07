"""Caching decorator for async functions using Redis.

Provides a ``@cached`` decorator that transparently caches the JSON-serializable
return value of an async function in Redis with a configurable TTL. Cache
failures are logged and swallowed to ensure graceful degradation.
"""

import functools
import json
import logging
from collections.abc import Callable, Coroutine
from dataclasses import asdict, is_dataclass
from typing import Any

logger = logging.getLogger(__name__)

Serializer = Callable[[Any], Any]
Deserializer = Callable[[Any], Any]


def _to_jsonable(value: Any) -> Any:
    """Convert a Python object into a JSON-serializable structure."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list | tuple | set):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def cached(
    ttl: int,
    key_builder: Callable[..., str],
    serializer: Serializer | None = None,
    deserializer: Deserializer | None = None,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    """Decorator that caches async function results in Redis.

    Args:
        ttl: Time-to-live in seconds for the cached value.
        key_builder: Callable that receives the same args as the decorated
            function and returns the Redis key string.
        serializer: Optional callable used before ``json.dumps``.
        deserializer: Optional callable used after ``json.loads``.
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
                    decoded = json.loads(cached_value)
                    if deserializer is not None:
                        try:
                            return deserializer(decoded)
                        except Exception:
                            logger.warning("Cache decode failed for key %s, refreshing value", key)
                            await redis.delete(key)
                    else:
                        return decoded
            except Exception:
                logger.warning("Cache read failed for key %s, proceeding without cache", key)

            result = await func(*args, **kwargs)

            try:
                redis = get_redis()
                payload = serializer(result) if serializer is not None else _to_jsonable(result)
                await redis.setex(key, ttl, json.dumps(payload))
            except Exception:
                logger.warning("Cache write failed for key %s", key)

            return result

        return wrapper

    return decorator
