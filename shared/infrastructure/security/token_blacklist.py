from shared.domain.interfaces.token_blacklist import ITokenBlacklist
from shared.infrastructure.cache.keys import token_blacklist_key
from shared.infrastructure.cache.redis_client import get_redis


class RedisTokenBlacklist(ITokenBlacklist):
    async def add(self, token_id: str, ttl_seconds: int) -> None:
        redis = get_redis()
        key = token_blacklist_key(token_id)
        await redis.setex(key, ttl_seconds, "1")

    async def is_blacklisted(self, token_id: str) -> bool:
        redis = get_redis()
        key = token_blacklist_key(token_id)
        return await redis.exists(key) == 1
