"""Get game DLCs use case."""

import asyncio
import contextlib
import logging

from modules.games.domain.entities.game_detail import DlcDetail
from modules.games.domain.entities.steam import SteamAppDetails
from modules.games.domain.interfaces.repositories.i_game_repository import IGameRepository
from modules.games.domain.interfaces.use_cases.get_game_dlcs import IGetGameDlcsUseCase
from shared.domain.interfaces.i_game_reader import IGameReader
from shared.domain.interfaces.steam_metadata_client import ISteamMetadataClient

logger = logging.getLogger(__name__)

_MAX_CONCURRENT_DLCS = 5


class GetGameDlcsUseCase(IGetGameDlcsUseCase):
    """Fetch DLC details for a Steam game and mark each as owned/unowned."""

    def __init__(
        self,
        repo: IGameRepository,
        steam_metadata: ISteamMetadataClient,
        game_reader: IGameReader,
    ) -> None:
        self._repo = repo
        self._steam_metadata = steam_metadata
        self._game_reader = game_reader

    async def execute(self, uid: str, game_id: str) -> list[DlcDetail]:
        game_doc = await self._repo.get_game(game_id)
        steam_app_id: int | None = game_doc.get("steam_app_id") if game_doc else None

        if steam_app_id is None and game_id.startswith("steam_"):
            with contextlib.suppress(ValueError):
                steam_app_id = int(game_id.split("_", 1)[1])

        if steam_app_id is None:
            return []

        # Get the DLC app ID list from base game details
        app_details = await self._steam_metadata.get_app_details(steam_app_id)
        if app_details is None or not app_details.dlc_app_ids:
            return []

        # Fetch DLC metadata in parallel (limited concurrency)
        semaphore = asyncio.Semaphore(_MAX_CONCURRENT_DLCS)

        async def _fetch(dlc_app_id: int) -> SteamAppDetails | None:
            async with semaphore:
                return await self._steam_metadata.get_app_details(dlc_app_id)

        results = await asyncio.gather(
            *[_fetch(dlc_id) for dlc_id in app_details.dlc_app_ids],
            return_exceptions=True,
        )

        owned_ids = await self._game_reader.get_owned_game_ids(uid)

        dlcs: list[DlcDetail] = []
        for dlc_app_id, result in zip(app_details.dlc_app_ids, results, strict=False):
            if isinstance(result, BaseException) or result is None:
                logger.warning("Failed to fetch DLC details for app_id %s", dlc_app_id)
                continue
            dlc_game_id = f"steam_{dlc_app_id}"
            dlcs.append(
                DlcDetail(
                    app_id=dlc_app_id,
                    name=result.name,
                    header_image=result.header_image,
                    is_owned=dlc_game_id in owned_ids,
                )
            )

        return dlcs
