"""Use case: sync the user's game library from external platforms."""

import asyncio
from typing import Any

from modules.library.domain.entities.library_game import LibraryGame
from modules.library.domain.interfaces.repositories.i_library_repository import (
    ILibraryRepository,
)
from modules.library.domain.interfaces.use_cases.sync_library import ISyncLibraryUseCase
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.epic_auth_client import IEpicAuthClient
from shared.domain.interfaces.gog_auth_client import IGogAuthClient
from shared.domain.interfaces.i_platform_reader import IPlatformReader
from shared.domain.interfaces.i_steam_library_source import ISteamLibrarySource
from shared.domain.interfaces.psn_auth_client import IPsnAuthClient


class SyncLibraryUseCase(ISyncLibraryUseCase):
    """Orchestrate a multi-platform library sync for the user."""

    def __init__(
        self,
        repo: ILibraryRepository,
        platform_reader: IPlatformReader,
        steam_library_source: ISteamLibrarySource,
        epic_client: IEpicAuthClient,
        gog_client: IGogAuthClient,
        psn_client: IPsnAuthClient,
    ) -> None:
        self._repo = repo
        self._platform_reader = platform_reader
        self._steam_library = steam_library_source
        self._epic_client = epic_client
        self._gog_client = gog_client
        self._psn_client = psn_client

    async def execute(self, uid: str, platform: Platform | None = None) -> int:
        linked_with_tokens = await self._platform_reader.get_linked_with_tokens(uid)
        if platform is not None:
            linked_with_tokens = [
                (lp, t) for lp, t in linked_with_tokens if lp.platform == platform
            ]

        results: list[Any] = await asyncio.gather(
            *[self._fetch_platform_games(lp, tokens) for lp, tokens in linked_with_tokens],
            return_exceptions=True,
        )

        all_games: list[LibraryGame] = []
        for result in results:
            if not isinstance(result, Exception):
                all_games.extend(result)

        if all_games:
            await self._repo.upsert_games(uid, all_games)

        return len(all_games)

    async def _fetch_platform_games(
        self, lp: LinkedPlatform, tokens: dict[str, Any]
    ) -> list[LibraryGame]:
        if lp.platform == Platform.STEAM:
            return await self._steam_library.get_owned_games(lp.username)

        if not tokens or not tokens.get("access_token"):
            return []

        if lp.platform == Platform.EPIC:
            account_id = tokens.get("account_id", "")
            epic_games: Any = await self._epic_client.fetch_library(
                tokens["access_token"], account_id
            )
            return [_normalize_epic(g) for g in epic_games]

        if lp.platform == Platform.GOG:
            gog_games: Any = await self._gog_client.get_user_games(tokens["access_token"])
            return [_normalize_gog(g) for g in gog_games]

        if lp.platform == Platform.PSN:
            psn_games: Any = await self._psn_client.get_played_games(tokens["access_token"])
            return [_normalize_psn(g) for g in psn_games]

        return []


def _normalize_epic(game: Any) -> LibraryGame:
    return LibraryGame(
        game_id=f"epic_{game.namespace}_{game.app_name}",
        title=game.app_name,
        platform=Platform.EPIC,
        extra={"namespace": game.namespace, "catalog_item_id": game.catalog_item_id},
    )


def _normalize_gog(game: Any) -> LibraryGame:
    return LibraryGame(
        game_id=f"gog_{game.id}",
        title=game.title,
        platform=Platform.GOG,
        cover_url=getattr(game, "image_url", None),
    )


def _normalize_psn(game: Any) -> LibraryGame:
    return LibraryGame(
        game_id=f"psn_{game.title_id}",
        title=game.name,
        platform=Platform.PSN,
        cover_url=getattr(game, "image_url", None),
        playtime_minutes=getattr(game, "play_duration_minutes", 0),
        last_played=getattr(game, "last_played_at", None),
    )
