from shared.domain.interfaces.cleanup_registry import ICleanupRegistry
from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.domain.interfaces.token_blacklist import ITokenBlacklist
from shared.domain.interfaces.user_repository import IUserRepository
from shared.infrastructure.cleanup_registry import CleanupRegistry
from shared.infrastructure.security.firebase_auth_provider import FirebaseAuthProvider
from shared.infrastructure.security.token_blacklist import RedisTokenBlacklist

_cleanup_registry = CleanupRegistry()


def get_firebase_auth_provider() -> IFirebaseAuthProvider:
    return FirebaseAuthProvider()


def get_token_blacklist() -> ITokenBlacklist:
    return RedisTokenBlacklist()


def get_cleanup_registry() -> ICleanupRegistry:
    return _cleanup_registry


def get_user_repository() -> IUserRepository:
    from modules.auth.infrastructure.repos.user_repository import FirestoreUserRepository

    return FirestoreUserRepository()
