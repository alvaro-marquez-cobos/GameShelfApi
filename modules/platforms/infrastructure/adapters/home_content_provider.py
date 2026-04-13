"""Adapter that exposes Steam as the home-screen content provider."""

import logging

from modules.platforms.domain.entities.steam import SteamChartsGame, SteamGame
from modules.platforms.domain.interfaces.services.i_steam_auth_client import ISteamAuthClient
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.popular_game import PopularGame
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.i_home_content_provider import IHomeContentProvider
from shared.domain.interfaces.i_platform_reader import IPlatformReader

logger = logging.getLogger(__name__)

_STEAM_HEADER_URL = (
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"
)


def _steam_game_to_library_game(game: SteamGame) -> LibraryGame:
    return LibraryGame(
        game_id=f"steam_{game.app_id}",
        title=game.name,
        platform=Platform.STEAM,
        cover_url=game.header_image or None,
        playtime_minutes=game.playtime_forever,
        last_played=str(game.last_played) if game.last_played else None,
        steam_app_id=game.app_id,
    )


def _charts_game_to_popular(game: SteamChartsGame) -> PopularGame:
    cover_url = _STEAM_HEADER_URL.format(app_id=game.app_id) if game.app_id else None
    return PopularGame(
        steam_app_id=game.app_id,
        title=game.name,
        current_players=game.current_players,
        cover_url=cover_url,
    )


class SteamHomeContentProvider(IHomeContentProvider):
    """Sources home-screen content from Steam via ``ISteamAuthClient``."""

    def __init__(
        self,
        steam_client: ISteamAuthClient,
        platform_reader: IPlatformReader,
    ) -> None:
        self._steam = steam_client
        self._platform_reader = platform_reader

    async def get_recently_played(self, uid: str) -> list[LibraryGame] | None:
        steam_id = await self._resolve_steam_id(uid)
        if steam_id is None:
            return None
        games = await self._steam.get_recently_played(steam_id)
        return [_steam_game_to_library_game(g) for g in games]

    async def get_globally_popular(self, limit: int) -> list[PopularGame]:
        games = await self._steam.get_most_played_global(limit=limit)
        return [_charts_game_to_popular(g) for g in games]

    async def _resolve_steam_id(self, uid: str) -> str | None:
        try:
            platforms = await self._platform_reader.get_linked_platforms(uid)
        except Exception:
            logger.debug("Failed to read linked platforms for uid=%s", uid)
            return None
        for lp in platforms:
            if lp.platform == Platform.STEAM:
                return lp.username
        return None
