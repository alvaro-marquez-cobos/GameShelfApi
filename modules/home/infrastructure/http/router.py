"""Home module HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from composition.dependencies import get_get_home_use_case
from composition.security import get_current_user
from modules.home.domain.interfaces.use_cases.get_home import IGetHomeUseCase
from modules.home.infrastructure.http.schemas import (
    HomeResponse,
    PopularGameResponse,
    PopularOnlyResponse,
)
from modules.library.infrastructure.http.schemas import LibraryGameResponse
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.user import AuthenticatedUser

router = APIRouter()


def _to_library_game(game: LibraryGame) -> LibraryGameResponse:
    return LibraryGameResponse(
        id=game.game_id,
        title=game.title,
        platform=game.platform,
        cover_url=game.cover_url,
        playtime_minutes=game.playtime_minutes,
        last_played=game.last_played,
        steam_app_id=game.steam_app_id,
    )


@router.get("", response_model=HomeResponse)
async def get_home(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetHomeUseCase, Depends(get_get_home_use_case)],
) -> HomeResponse:
    data = await use_case.execute(current_user.uid)
    recently = None
    if data.recently_played is not None:
        recently = [_to_library_game(game) for game in data.recently_played]

    popular = [
        PopularGameResponse(
            game_id=game.game_id,
            steam_app_id=game.steam_app_id,
            title=game.title,
            current_players=game.current_players,
            cover_url=game.cover_url,
        )
        for game in data.popular_now
    ]

    return HomeResponse(
        recently_played=recently,
        most_played=[_to_library_game(game) for game in data.most_played],
        popular_now=popular,
    )


@router.get("/popular", response_model=PopularOnlyResponse)
async def get_popular(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetHomeUseCase, Depends(get_get_home_use_case)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PopularOnlyResponse:
    data = await use_case.execute(current_user.uid)
    popular_now = data.popular_now or []
    games = [
        PopularGameResponse(
            game_id=game.game_id,
            steam_app_id=game.steam_app_id,
            title=game.title,
            current_players=game.current_players,
            cover_url=game.cover_url,
        )
        for game in popular_now[:limit]
    ]
    return PopularOnlyResponse(games=games)
