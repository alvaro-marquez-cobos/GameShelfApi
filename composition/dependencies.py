"""Dependency injection factories for FastAPI's Depends() system.

This module is the single wiring point where interfaces are bound to their
concrete implementations.
"""

from typing import Annotated

from fastapi import Depends

from modules.auth.application.delete_account_use_case import DeleteAccountUseCase
from modules.auth.application.get_profile_use_case import GetProfileUseCase
from modules.auth.application.logout_use_case import LogoutUseCase
from modules.auth.application.sync_user_use_case import SyncUserUseCase
from modules.auth.domain.interfaces.use_cases.delete_account import IDeleteAccountUseCase
from modules.auth.domain.interfaces.use_cases.get_profile import IGetProfileUseCase
from modules.auth.domain.interfaces.use_cases.logout import ILogoutUseCase
from modules.auth.domain.interfaces.use_cases.sync_user import ISyncUserUseCase
from modules.auth.infrastructure.repos.user_repository import FirestoreUserRepository
from modules.games.infrastructure.clients.hltb_client import HltbClient
from modules.games.infrastructure.clients.itad_client import ItadClient
from modules.games.infrastructure.clients.protondb_client import ProtonDbClient
from modules.games.infrastructure.clients.steam_metadata_client import SteamMetadataClient
from modules.platforms.infrastructure.clients.epic_auth_client import EpicAuthClient
from modules.platforms.infrastructure.clients.gog_auth_client import GogAuthClient
from modules.platforms.infrastructure.clients.psn_auth_client import PsnAuthClient
from modules.platforms.infrastructure.clients.steam_auth_client import SteamAuthClient
from modules.platforms.infrastructure.repos.platform_repository import (
    FirestorePlatformRepository,
)
from modules.wishlist.infrastructure.repos.wishlist_repository import (
    FirestoreWishlistRepository,
)
from shared.domain.interfaces.cleanup_registry import ICleanupRegistry
from shared.domain.interfaces.epic_auth_client import IEpicAuthClient
from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.domain.interfaces.gog_auth_client import IGogAuthClient
from shared.domain.interfaces.hltb_client import IHltbClient
from shared.domain.interfaces.i_platform_reader import IPlatformReader
from shared.domain.interfaces.i_wishlist_reader import IWishlistReader
from shared.domain.interfaces.itad_client import IItadClient
from shared.domain.interfaces.protondb_client import IProtonDbClient
from shared.domain.interfaces.psn_auth_client import IPsnAuthClient
from shared.domain.interfaces.steam_auth_client import ISteamAuthClient
from shared.domain.interfaces.steam_metadata_client import ISteamMetadataClient
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
    return FirestoreUserRepository()


def get_sync_user_use_case(
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> ISyncUserUseCase:
    return SyncUserUseCase(user_repository)


def get_logout_use_case(
    firebase_auth: Annotated[IFirebaseAuthProvider, Depends(get_firebase_auth_provider)],
    token_blacklist: Annotated[ITokenBlacklist, Depends(get_token_blacklist)],
) -> ILogoutUseCase:
    return LogoutUseCase(firebase_auth, token_blacklist)


def get_delete_account_use_case(
    cleanup_registry: Annotated[ICleanupRegistry, Depends(get_cleanup_registry)],
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
    firebase_auth: Annotated[IFirebaseAuthProvider, Depends(get_firebase_auth_provider)],
) -> IDeleteAccountUseCase:
    return DeleteAccountUseCase(cleanup_registry, user_repository, firebase_auth)


def get_get_profile_use_case(
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> IGetProfileUseCase:
    return GetProfileUseCase(user_repository)


# ---------------------------------------------------------------------------
# Platform repository
# ---------------------------------------------------------------------------


def get_platform_repository() -> FirestorePlatformRepository:
    return FirestorePlatformRepository()


def get_platform_reader(
    repo: Annotated[FirestorePlatformRepository, Depends(get_platform_repository)],
) -> IPlatformReader:
    return repo


# ---------------------------------------------------------------------------
# Wishlist repository
# ---------------------------------------------------------------------------


def get_wishlist_repository() -> FirestoreWishlistRepository:
    return FirestoreWishlistRepository()


def get_wishlist_reader(
    repo: Annotated[FirestoreWishlistRepository, Depends(get_wishlist_repository)],
) -> IWishlistReader:
    return repo


# ---------------------------------------------------------------------------
# Platform auth clients
# ---------------------------------------------------------------------------


def get_steam_auth_client() -> ISteamAuthClient:
    return SteamAuthClient()


def get_epic_auth_client() -> IEpicAuthClient:
    return EpicAuthClient()


def get_gog_auth_client() -> IGogAuthClient:
    return GogAuthClient()


def get_psn_auth_client() -> IPsnAuthClient:
    return PsnAuthClient()


# ---------------------------------------------------------------------------
# Game data clients
# ---------------------------------------------------------------------------


def get_steam_metadata_client() -> ISteamMetadataClient:
    return SteamMetadataClient()


def get_protondb_client() -> IProtonDbClient:
    return ProtonDbClient()


def get_hltb_client() -> IHltbClient:
    return HltbClient()


def get_itad_client() -> IItadClient:
    return ItadClient()
