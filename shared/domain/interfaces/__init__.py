from shared.domain.interfaces.cleanup_registry import ICleanupRegistry
from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.domain.interfaces.i_game_reader import IGameReader
from shared.domain.interfaces.i_platform_reader import IPlatformReader
from shared.domain.interfaces.i_wishlist_reader import IWishlistReader
from shared.domain.interfaces.token_blacklist import ITokenBlacklist
from shared.domain.interfaces.user_repository import IUserRepository

__all__ = [
    "ICleanupRegistry",
    "IFirebaseAuthProvider",
    "IGameReader",
    "IPlatformReader",
    "ITokenBlacklist",
    "IUserRepository",
    "IWishlistReader",
]
