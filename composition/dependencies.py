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
from modules.games.application.get_game_detail_use_case import GetGameDetailUseCase
from modules.games.application.get_game_dlcs_use_case import GetGameDlcsUseCase
from modules.games.domain.interfaces.use_cases.get_game_detail import IGetGameDetailUseCase
from modules.games.domain.interfaces.use_cases.get_game_dlcs import IGetGameDlcsUseCase
from modules.games.infrastructure.clients.hltb_client import HltbClient
from modules.games.infrastructure.clients.itad_client import ItadClient
from modules.games.infrastructure.clients.protondb_client import ProtonDbClient
from modules.games.infrastructure.clients.steam_metadata_client import SteamMetadataClient
from modules.games.infrastructure.repos.game_repository import FirestoreGameRepository
from modules.home.application.get_home_use_case import GetHomeUseCase
from modules.home.domain.interfaces.use_cases.get_home import IGetHomeUseCase
from modules.library.application.get_library_stats_use_case import GetLibraryStatsUseCase
from modules.library.application.get_library_use_case import GetLibraryUseCase
from modules.library.application.sync_library_use_case import SyncLibraryUseCase
from modules.library.domain.interfaces.repositories.i_library_repository import (
    ILibraryRepository,
)
from modules.library.domain.interfaces.use_cases.get_library import IGetLibraryUseCase
from modules.library.domain.interfaces.use_cases.get_library_stats import (
    IGetLibraryStatsUseCase,
)
from modules.library.domain.interfaces.use_cases.sync_library import ISyncLibraryUseCase
from modules.library.infrastructure.repos.library_repository import (
    FirestoreLibraryRepository,
)
from modules.platforms.application.get_linked_platforms_use_case import (
    GetLinkedPlatformsUseCase,
)
from modules.platforms.application.link_epic_use_case import LinkEpicUseCase
from modules.platforms.application.link_gog_use_case import LinkGogUseCase
from modules.platforms.application.link_psn_use_case import LinkPsnUseCase
from modules.platforms.application.link_steam_use_case import LinkSteamUseCase
from modules.platforms.application.unlink_platform_use_case import UnlinkPlatformUseCase
from modules.platforms.domain.interfaces.use_cases.get_linked_platforms import (
    IGetLinkedPlatformsUseCase,
)
from modules.platforms.domain.interfaces.use_cases.link_epic import ILinkEpicUseCase
from modules.platforms.domain.interfaces.use_cases.link_gog import ILinkGogUseCase
from modules.platforms.domain.interfaces.use_cases.link_psn import ILinkPsnUseCase
from modules.platforms.domain.interfaces.use_cases.link_steam import ILinkSteamUseCase
from modules.platforms.domain.interfaces.use_cases.unlink_platform import (
    IUnlinkPlatformUseCase,
)
from modules.platforms.infrastructure.clients.epic_auth_client import EpicAuthClient
from modules.platforms.infrastructure.clients.gog_auth_client import GogAuthClient
from modules.platforms.infrastructure.clients.psn_auth_client import PsnAuthClient
from modules.platforms.infrastructure.clients.steam_auth_client import SteamAuthClient
from modules.platforms.infrastructure.repos.platform_repository import (
    FirestorePlatformRepository,
)
from modules.search.application.search_use_case import SearchGamesUseCase
from modules.search.domain.interfaces.use_cases.search_games import ISearchGamesUseCase
from modules.wishlist.application.add_to_wishlist_use_case import AddToWishlistUseCase
from modules.wishlist.application.check_wishlist_use_case import CheckWishlistUseCase
from modules.wishlist.application.get_wishlist_use_case import GetWishlistUseCase
from modules.wishlist.application.remove_from_wishlist_use_case import (
    RemoveFromWishlistUseCase,
)
from modules.wishlist.domain.interfaces.use_cases.add_to_wishlist import IAddToWishlistUseCase
from modules.wishlist.domain.interfaces.use_cases.check_wishlist import ICheckWishlistUseCase
from modules.wishlist.domain.interfaces.use_cases.get_wishlist import IGetWishlistUseCase
from modules.wishlist.domain.interfaces.use_cases.remove_from_wishlist import (
    IRemoveFromWishlistUseCase,
)
from modules.wishlist.infrastructure.repos.wishlist_repository import (
    FirestoreWishlistRepository,
)
from shared.domain.interfaces.cleanup_registry import ICleanupRegistry
from shared.domain.interfaces.epic_auth_client import IEpicAuthClient
from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.domain.interfaces.gog_auth_client import IGogAuthClient
from shared.domain.interfaces.hltb_client import IHltbClient
from shared.domain.interfaces.i_game_reader import IGameReader
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


# ---------------------------------------------------------------------------
# Auth infrastructure
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Library repository and use cases
# (after platform clients — sync use case depends on them)
# ---------------------------------------------------------------------------


def get_library_repository() -> FirestoreLibraryRepository:
    return FirestoreLibraryRepository()


def get_game_reader(
    repo: Annotated[FirestoreLibraryRepository, Depends(get_library_repository)],
) -> IGameReader:
    return repo


def get_get_library_use_case(
    repo: Annotated[FirestoreLibraryRepository, Depends(get_library_repository)],
) -> IGetLibraryUseCase:
    return GetLibraryUseCase(repo)


def get_sync_library_use_case(
    repo: Annotated[FirestoreLibraryRepository, Depends(get_library_repository)],
    platform_reader: Annotated[IPlatformReader, Depends(get_platform_reader)],
    steam_client: Annotated[ISteamAuthClient, Depends(get_steam_auth_client)],
    epic_client: Annotated[IEpicAuthClient, Depends(get_epic_auth_client)],
    gog_client: Annotated[IGogAuthClient, Depends(get_gog_auth_client)],
    psn_client: Annotated[IPsnAuthClient, Depends(get_psn_auth_client)],
) -> ISyncLibraryUseCase:
    return SyncLibraryUseCase(
        repo, platform_reader, steam_client, epic_client, gog_client, psn_client
    )


def get_get_library_stats_use_case(
    repo: Annotated[FirestoreLibraryRepository, Depends(get_library_repository)],
) -> IGetLibraryStatsUseCase:
    return GetLibraryStatsUseCase(repo)


# ---------------------------------------------------------------------------
# Wishlist use cases
# ---------------------------------------------------------------------------


def get_get_wishlist_use_case(
    repo: Annotated[FirestoreWishlistRepository, Depends(get_wishlist_repository)],
    itad_client: Annotated[IItadClient, Depends(get_itad_client)],
) -> IGetWishlistUseCase:
    return GetWishlistUseCase(repo, itad_client)


def get_add_to_wishlist_use_case(
    repo: Annotated[FirestoreWishlistRepository, Depends(get_wishlist_repository)],
) -> IAddToWishlistUseCase:
    return AddToWishlistUseCase(repo)


def get_remove_from_wishlist_use_case(
    repo: Annotated[FirestoreWishlistRepository, Depends(get_wishlist_repository)],
) -> IRemoveFromWishlistUseCase:
    return RemoveFromWishlistUseCase(repo)


def get_check_wishlist_use_case(
    repo: Annotated[FirestoreWishlistRepository, Depends(get_wishlist_repository)],
) -> ICheckWishlistUseCase:
    return CheckWishlistUseCase(repo)


# ---------------------------------------------------------------------------
# Games repository and use cases
# ---------------------------------------------------------------------------


def get_game_repository() -> FirestoreGameRepository:
    return FirestoreGameRepository()


def get_get_game_detail_use_case(
    repo: Annotated[FirestoreGameRepository, Depends(get_game_repository)],
    steam_metadata: Annotated[ISteamMetadataClient, Depends(get_steam_metadata_client)],
    protondb: Annotated[IProtonDbClient, Depends(get_protondb_client)],
    hltb: Annotated[IHltbClient, Depends(get_hltb_client)],
    itad: Annotated[IItadClient, Depends(get_itad_client)],
    wishlist_reader: Annotated[IWishlistReader, Depends(get_wishlist_reader)],
) -> IGetGameDetailUseCase:
    return GetGameDetailUseCase(repo, steam_metadata, protondb, hltb, itad, wishlist_reader)


def get_get_game_dlcs_use_case(
    repo: Annotated[FirestoreGameRepository, Depends(get_game_repository)],
    steam_metadata: Annotated[ISteamMetadataClient, Depends(get_steam_metadata_client)],
    game_reader: Annotated[IGameReader, Depends(get_game_reader)],
) -> IGetGameDlcsUseCase:
    return GetGameDlcsUseCase(repo, steam_metadata, game_reader)


# ---------------------------------------------------------------------------
# Search use case
# ---------------------------------------------------------------------------


def get_search_games_use_case(
    itad_client: Annotated[IItadClient, Depends(get_itad_client)],
    game_reader: Annotated[IGameReader, Depends(get_game_reader)],
    wishlist_reader: Annotated[IWishlistReader, Depends(get_wishlist_reader)],
) -> ISearchGamesUseCase:
    return SearchGamesUseCase(itad_client, game_reader, wishlist_reader)


# ---------------------------------------------------------------------------
# Platform use cases
# ---------------------------------------------------------------------------


def get_get_linked_platforms_use_case(
    repo: Annotated[FirestorePlatformRepository, Depends(get_platform_repository)],
) -> IGetLinkedPlatformsUseCase:
    return GetLinkedPlatformsUseCase(repo)


def get_link_steam_use_case(
    steam_client: Annotated[ISteamAuthClient, Depends(get_steam_auth_client)],
    repo: Annotated[FirestorePlatformRepository, Depends(get_platform_repository)],
) -> ILinkSteamUseCase:
    return LinkSteamUseCase(steam_client, repo)


def get_link_epic_use_case(
    epic_client: Annotated[IEpicAuthClient, Depends(get_epic_auth_client)],
    repo: Annotated[FirestorePlatformRepository, Depends(get_platform_repository)],
) -> ILinkEpicUseCase:
    return LinkEpicUseCase(epic_client, repo)


def get_link_gog_use_case(
    gog_client: Annotated[IGogAuthClient, Depends(get_gog_auth_client)],
    repo: Annotated[FirestorePlatformRepository, Depends(get_platform_repository)],
) -> ILinkGogUseCase:
    return LinkGogUseCase(gog_client, repo)


def get_link_psn_use_case(
    psn_client: Annotated[IPsnAuthClient, Depends(get_psn_auth_client)],
    repo: Annotated[FirestorePlatformRepository, Depends(get_platform_repository)],
) -> ILinkPsnUseCase:
    return LinkPsnUseCase(psn_client, repo)


def get_unlink_platform_use_case(
    repo: Annotated[FirestorePlatformRepository, Depends(get_platform_repository)],
) -> IUnlinkPlatformUseCase:
    return UnlinkPlatformUseCase(repo)


# ---------------------------------------------------------------------------
# Home use case
# ---------------------------------------------------------------------------


def get_get_home_use_case(
    steam_client: Annotated[ISteamAuthClient, Depends(get_steam_auth_client)],
    library_repo: Annotated[ILibraryRepository, Depends(get_library_repository)],
    platform_reader: Annotated[IPlatformReader, Depends(get_platform_reader)],
) -> IGetHomeUseCase:
    return GetHomeUseCase(steam_client, library_repo, platform_reader)
