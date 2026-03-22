def token_blacklist_key(token_id: str) -> str:
    return f"blacklist:{token_id}"


def user_cache_key(uid: str) -> str:
    return f"user:{uid}"
