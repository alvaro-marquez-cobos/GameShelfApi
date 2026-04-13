"""Adapter that exposes Steam-owned games as generic LibraryGame entities."""

from datetime import UTC, datetime

from modules.platforms.domain.entities.steam import SteamGame
from modules.platforms.domain.interfaces.services.i_steam_auth_client import ISteamAuthClient
from shared.domain.entities.library_game import LibraryGame
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.i_steam_library_source import ISteamLibrarySource


def _to_library_game(game: SteamGame) -> LibraryGame:
    last_played: str | None = None
    if game.last_played:
        last_played = datetime.fromtimestamp(game.last_played, tz=UTC).isoformat()
    return LibraryGame(
        game_id=f"steam_{game.app_id}",
        title=game.name,
        platform=Platform.STEAM,
        cover_url=game.header_image or None,
        playtime_minutes=game.playtime_forever,
        last_played=last_played,
        steam_app_id=game.app_id,
    )


class SteamLibrarySource(ISteamLibrarySource):
    """Adapts ``ISteamAuthClient`` to the generic ``ISteamLibrarySource`` contract."""

    def __init__(self, steam_client: ISteamAuthClient) -> None:
        self._steam = steam_client

    async def get_owned_games(self, steam_id: str) -> list[LibraryGame]:
        games = await self._steam.get_owned_games(steam_id)
        return [_to_library_game(g) for g in games]
