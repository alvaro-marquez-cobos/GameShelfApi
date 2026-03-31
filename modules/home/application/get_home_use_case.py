"""Get home screen data use case."""

import asyncio
import logging
from typing import Any

from modules.home.domain.entities.home_data import HomeData, PopularGame
from modules.home.domain.interfaces.use_cases.get_home import IGetHomeUseCase
from shared.domain.entities.library_game import LibraryGame
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.i_library_reader import ILibraryReader
from shared.domain.interfaces.i_platform_reader import IPlatformReader
from shared.domain.interfaces.steam_auth_client import ISteamAuthClient

logger = logging.getLogger(__name__)

_MOST_PLAYED_LIMIT = 5
_POPULAR_LIMIT = 20


def _steam_game_to_library_game(game: Any) -> LibraryGame:
    """Convert a SteamGame duck-typed object to a LibraryGame."""
    return LibraryGame(
        game_id=f"steam_{game.app_id}",
        title=game.name,
        platform=Platform.STEAM,
        cover_url=game.header_image or None,
        playtime_minutes=game.playtime_forever,
        last_played=str(game.last_played) if game.last_played else None,
        steam_app_id=game.app_id,
    )


def _steam_game_to_popular(game: Any) -> PopularGame:
    """Convert a SteamGame duck-typed object to a PopularGame."""
    return PopularGame(
        steam_app_id=game.app_id,
        title=game.name,
        current_players=game.playtime_forever,
        cover_url=game.header_image or None,
    )


class GetHomeUseCase(IGetHomeUseCase):
    """Assemble home screen data from Steam and the user's library."""

    def __init__(
        self,
        steam_client: ISteamAuthClient,
        library_reader: ILibraryReader,
        platform_reader: IPlatformReader,
    ) -> None:
        self._steam = steam_client
        self._library = library_reader
        self._platform_reader = platform_reader

    async def execute(self, uid: str) -> HomeData:
        # Resolve Steam ID for per-user sections
        steam_id = await self._get_steam_id(uid)

        async def _no_recently_played() -> None:
            return None

        recently_played_coro = (
            self._steam.get_recently_played(steam_id) if steam_id else _no_recently_played()
        )
        results = await asyncio.gather(
            recently_played_coro,
            self._library.get_games(uid),
            self._steam.get_most_played_global(limit=_POPULAR_LIMIT),
            return_exceptions=True,
        )

        # Recently played
        recently_played_raw = results[0]
        recently_played: list[LibraryGame] | None
        if steam_id is None:
            recently_played = None
        elif isinstance(recently_played_raw, BaseException):
            logger.warning("Failed to fetch recently played: %s", recently_played_raw)
            recently_played = None
        elif isinstance(recently_played_raw, list):
            recently_played = [_steam_game_to_library_game(g) for g in recently_played_raw]
        else:
            recently_played = None

        # Most played (from library)
        library_raw = results[1]
        most_played: list[LibraryGame]
        if isinstance(library_raw, BaseException):
            logger.warning("Failed to fetch library: %s", library_raw)
            most_played = []
        else:
            sorted_games = sorted(library_raw, key=lambda g: g.playtime_minutes, reverse=True)
            most_played = sorted_games[:_MOST_PLAYED_LIMIT]

        # Popular now (global)
        popular_raw = results[2]
        popular_now: list[PopularGame] | None
        if isinstance(popular_raw, BaseException):
            logger.warning("Failed to fetch global popular games: %s", popular_raw)
            popular_now = None
        else:
            popular_now = [_steam_game_to_popular(g) for g in popular_raw]

        return HomeData(
            recently_played=recently_played,
            most_played=most_played,
            popular_now=popular_now,
        )

    async def _get_steam_id(self, uid: str) -> str | None:
        """Return the user's Steam ID from linked platforms, or None."""
        try:
            platforms = await self._platform_reader.get_linked_platforms(uid)
        except Exception:
            return None
        for lp in platforms:
            if lp.platform == Platform.STEAM:
                return lp.username
        return None
