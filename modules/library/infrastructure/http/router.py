"""Library module HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from composition.dependencies import (
    get_get_library_stats_use_case,
    get_get_library_use_case,
    get_sync_library_use_case,
)
from composition.security import get_current_user
from modules.library.domain.enums.library import LibrarySortBy, LibraryTab
from modules.library.domain.interfaces.use_cases.get_library import IGetLibraryUseCase
from modules.library.domain.interfaces.use_cases.get_library_stats import IGetLibraryStatsUseCase
from modules.library.domain.interfaces.use_cases.sync_library import ISyncLibraryUseCase
from modules.library.infrastructure.http.schemas import (
    GetLibraryResponse,
    LibraryGameResponse,
    LibraryStatsResponse,
    MergedLibraryGameResponse,
    SyncLibraryRequest,
    SyncLibraryResponse,
)
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.user import AuthenticatedUser
from shared.domain.enums.platform import Platform

router = APIRouter()


def _build_portrait_url(steam_app_id: int | None) -> str | None:
    if steam_app_id is None:
        return None
    return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_app_id}/library_600x900.jpg"


def _to_game_response(game: LibraryGame) -> LibraryGameResponse:
    return LibraryGameResponse(
        id=game.game_id,
        title=game.title,
        platform=game.platform,
        cover_url=game.cover_url,
        portrait_cover_url=_build_portrait_url(game.steam_app_id),
        playtime_minutes=game.playtime_minutes,
        last_played=game.last_played,
        steam_app_id=game.steam_app_id,
        game_type=game.game_type,
        parent_game_id=game.parent_game_id,
    )


def _to_merged_response(game: LibraryGame, platforms: list[Platform]) -> MergedLibraryGameResponse:
    return MergedLibraryGameResponse(
        game=_to_game_response(game),
        platforms=platforms,
    )


@router.get("", response_model=GetLibraryResponse)
async def get_library(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetLibraryUseCase, Depends(get_get_library_use_case)],
    tab: Annotated[LibraryTab, Query()] = LibraryTab.ALL,
    sort: Annotated[LibrarySortBy, Query()] = LibrarySortBy.ALPHABETICAL,
    search: Annotated[str, Query()] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = 200,
    platforms: Annotated[list[Platform] | None, Query()] = None,
) -> GetLibraryResponse:
    offset = (page - 1) * page_size
    games, total, platforms_list = await use_case.execute(
        uid=current_user.uid,
        tab=tab,
        sort_by=sort,
        search=search,
        offset=offset,
        limit=page_size,
        platforms=platforms,
    )
    merged_games = [_to_merged_response(game, platforms_list[i]) for i, game in enumerate(games)]
    return GetLibraryResponse(
        games=merged_games,
        total=total,
        has_more=(offset + len(games)) < total,
    )


@router.get("/stats", response_model=LibraryStatsResponse)
async def get_library_stats(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetLibraryStatsUseCase, Depends(get_get_library_stats_use_case)],
) -> LibraryStatsResponse:
    stats = await use_case.execute(current_user.uid)
    return LibraryStatsResponse(
        total_games=stats.total,
        pc_games=stats.pc_games,
        console_games=stats.console_games,
        total_playtime=stats.total_playtime_hours,
        total_unique=stats.total_unique,
        pc_unique=stats.pc_unique,
        console_unique=stats.console_unique,
    )


@router.post("/sync", response_model=SyncLibraryResponse)
async def sync_library(
    body: SyncLibraryRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ISyncLibraryUseCase, Depends(get_sync_library_use_case)],
) -> SyncLibraryResponse:
    synced = await use_case.execute(current_user.uid, body.platform)
    return SyncLibraryResponse(synced=synced)
