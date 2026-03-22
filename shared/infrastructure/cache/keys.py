"""Redis key builders for consistent cache key formatting.

All cache keys should be generated through these functions to ensure
naming consistency and easy auditing of key patterns.
"""


def token_blacklist_key(token_id: str) -> str:
    """Build the Redis key for a blacklisted token entry."""
    return f"blacklist:{token_id}"


def user_cache_key(uid: str) -> str:
    """Build the Redis key for a cached user profile."""
    return f"user:{uid}"
