"""Dependency injection factories for FastAPI's Depends() system.

This module is the single wiring point where interfaces are bound to their
concrete implementations. Use cases and infrastructure services are lazily
imported to avoid circular dependencies between modules.
"""

from typing import Annotated

from fastapi import Depends

from modules.auth.domain.interfaces.use_cases.delete_account import IDeleteAccountUseCase
from modules.auth.domain.interfaces.use_cases.get_profile import IGetProfileUseCase
from modules.auth.domain.interfaces.use_cases.logout import ILogoutUseCase
from modules.auth.domain.interfaces.use_cases.sync_user import ISyncUserUseCase
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


def get_sync_user_use_case(
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> ISyncUserUseCase:
    from modules.auth.application.sync_user_use_case import SyncUserUseCase

    return SyncUserUseCase(user_repository)


def get_logout_use_case(
    firebase_auth: Annotated[IFirebaseAuthProvider, Depends(get_firebase_auth_provider)],
    token_blacklist: Annotated[ITokenBlacklist, Depends(get_token_blacklist)],
) -> ILogoutUseCase:
    from modules.auth.application.logout_use_case import LogoutUseCase

    return LogoutUseCase(firebase_auth, token_blacklist)


def get_delete_account_use_case(
    cleanup_registry: Annotated[ICleanupRegistry, Depends(get_cleanup_registry)],
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
    firebase_auth: Annotated[IFirebaseAuthProvider, Depends(get_firebase_auth_provider)],
) -> IDeleteAccountUseCase:
    from modules.auth.application.delete_account_use_case import DeleteAccountUseCase

    return DeleteAccountUseCase(cleanup_registry, user_repository, firebase_auth)


def get_get_profile_use_case(
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> IGetProfileUseCase:
    from modules.auth.application.get_profile_use_case import GetProfileUseCase

    return GetProfileUseCase(user_repository)
