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


# ---------------------------------------------------------------------------
# Game data keys (global scope — shared across all users)
# ---------------------------------------------------------------------------


def popular_games_key(limit: int) -> str:
    """Build the Redis key for the popular games list.

    TTL: 15 minutes.
    """
    return f"popular:games:{limit}"


def protondb_key(steam_app_id: str | int) -> str:
    """Build the Redis key for a ProtonDB rating entry.

    TTL: 1 hour.
    """
    return f"protondb:{steam_app_id}"


def hltb_key(normalized_title: str) -> str:
    """Build the Redis key for a HowLongToBeat duration result.

    TTL: 1 hour.
    """
    return f"hltb:{normalized_title}"


def hltb_token_key() -> str:
    """Build the Redis key for the HLTB session token.

    TTL: 25 minutes.
    """
    return "hltb:token"


def itad_info_key(itad_game_id: str) -> str:
    """Build the Redis key for an IsThereAnyDeal game info entry.

    TTL: 15 minutes.
    """
    return f"itad:info:{itad_game_id}"


def itad_lookup_key(normalized_title: str) -> str:
    """Build the Redis key for an ITAD game ID lookup by title.

    TTL: 1 hour.
    """
    return f"itad:lookup:{normalized_title}"


def steam_app_key(app_id: str | int) -> str:
    """Build the Redis key for Steam app details.

    TTL: 1 hour.
    """
    return f"steam:app:{app_id}"


def search_key(normalized_query: str) -> str:
    """Build the Redis key for a game search result set.

    TTL: 10 minutes.
    """
    return f"search:{normalized_query}"


# ---------------------------------------------------------------------------
# Per-user keys
# ---------------------------------------------------------------------------


def user_library_key(user_id: str) -> str:
    """Build the Redis key for a user's game library.

    TTL: 2 minutes.
    """
    return f"user:{user_id}:library"


def user_wishlist_ids_key(user_id: str) -> str:
    """Build the Redis key for a user's wishlist game ID set.

    TTL: 5 minutes.
    """
    return f"user:{user_id}:wishlist:ids"


def user_home_key(user_id: str) -> str:
    """Build the Redis key for a user's home section data.

    TTL: 5 minutes.
    """
    return f"user:{user_id}:home"
