"""Tests for Redis cache decorator behavior."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from shared.infrastructure.cache.decorators import cached


@dataclass(frozen=True)
class _SampleEntity:
    value: int


@pytest.mark.asyncio
async def test_cached_serializes_and_deserializes_dataclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = MagicMock()
    redis.get = AsyncMock(side_effect=[None, '{"value": 7}'])
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)

    import shared.infrastructure.cache.redis_client as redis_client

    monkeypatch.setattr(redis_client, "get_redis", lambda: redis)

    calls = 0

    @cached(
        ttl=60,
        key_builder=lambda cache_key: cache_key,
        deserializer=lambda data: _SampleEntity(**data) if data is not None else None,
    )
    async def fetch(cache_key: str) -> _SampleEntity:
        nonlocal calls
        calls += 1
        return _SampleEntity(value=7)

    first = await fetch("sample:key")
    second = await fetch("sample:key")

    assert first == _SampleEntity(value=7)
    assert second == _SampleEntity(value=7)
    assert calls == 1

    redis.setex.assert_awaited_once()
    setex_args = redis.setex.await_args.args
    assert setex_args[0] == "sample:key"
    assert setex_args[1] == 60
    assert setex_args[2] == '{"value": 7}'


@pytest.mark.asyncio
async def test_cached_refreshes_when_deserializer_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = MagicMock()
    redis.get = AsyncMock(return_value='{"bad": true}')
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)

    import shared.infrastructure.cache.redis_client as redis_client

    monkeypatch.setattr(redis_client, "get_redis", lambda: redis)

    calls = 0

    @cached(
        ttl=30,
        key_builder=lambda cache_key: cache_key,
        deserializer=lambda data: _SampleEntity(value=int(data["value"])),
    )
    async def fetch(cache_key: str) -> _SampleEntity:
        nonlocal calls
        calls += 1
        return _SampleEntity(value=11)

    result = await fetch("sample:broken")

    assert result == _SampleEntity(value=11)
    assert calls == 1
    redis.delete.assert_awaited_once_with("sample:broken")
    redis.setex.assert_awaited_once()
