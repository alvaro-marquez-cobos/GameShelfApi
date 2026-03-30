"""Get game detail use case — 3-phase enrichment."""

import asyncio
import contextlib
import logging
from typing import Any

from modules.games.domain.entities.game_detail import GameDetail
from modules.games.domain.entities.itad import Deal
from modules.games.domain.interfaces.repositories.i_game_repository import IGameRepository
from modules.games.domain.interfaces.use_cases.get_game_detail import IGetGameDetailUseCase
from shared.domain.interfaces.hltb_client import IHltbClient
from shared.domain.interfaces.i_wishlist_reader import IWishlistReader
from shared.domain.interfaces.itad_client import IItadClient
from shared.domain.interfaces.protondb_client import IProtonDbClient
from shared.domain.interfaces.steam_metadata_client import ISteamMetadataClient

logger = logging.getLogger(__name__)


def _ok(result: Any, default: Any) -> Any:
    """Return *result* if it is not an exception, otherwise *default*."""
    return default if isinstance(result, BaseException) else result


class GetGameDetailUseCase(IGetGameDetailUseCase):
    """Fetch and assemble enriched game detail from multiple services.

    Phase 1 — Resolve Steam app ID (if not already stored).
    Phase 2 — Parallel enrichment: Steam metadata, ProtonDB, HLTB, ITAD deals,
               wishlist flag.
    Phase 3 — Assemble and return GameDetail with graceful null for failures.
    """

    def __init__(
        self,
        repo: IGameRepository,
        steam_metadata: ISteamMetadataClient,
        protondb: IProtonDbClient,
        hltb: IHltbClient,
        itad: IItadClient,
        wishlist_reader: IWishlistReader,
    ) -> None:
        self._repo = repo
        self._steam_metadata = steam_metadata
        self._protondb = protondb
        self._hltb = hltb
        self._itad = itad
        self._wishlist_reader = wishlist_reader

    async def execute(self, uid: str, game_id: str, title: str) -> GameDetail:
        # ------------------------------------------------------------------
        # Phase 1 — Resolve Steam app ID
        # ------------------------------------------------------------------
        game_doc = await self._repo.get_game(game_id)
        steam_app_id: int | None = game_doc.get("steam_app_id") if game_doc else None

        if steam_app_id is None and game_id.startswith("steam_"):
            # Try to extract from deterministic game_id (e.g. "steam_570")
            with contextlib.suppress(ValueError):
                steam_app_id = int(game_id.split("_", 1)[1])

        if steam_app_id is None:
            # Fall back to Steam Store search by title
            try:
                steam_app_id = await self._steam_metadata.search_store(title)
            except Exception:
                logger.warning("Steam store search failed for '%s'", title)

        if steam_app_id is not None:
            try:
                await self._repo.update_steam_app_id(game_id, steam_app_id)
            except Exception:
                logger.warning("Failed to persist steam_app_id for '%s'", game_id)

        # ------------------------------------------------------------------
        # Phase 2 — Parallel enrichment (only if steam_app_id is resolved)
        # ------------------------------------------------------------------
        if steam_app_id is not None:
            results = await asyncio.gather(
                self._steam_metadata.get_app_details(steam_app_id),
                self._protondb.get_compatibility_rating(str(steam_app_id)),
                self._hltb.get_game_duration(title),
                self._get_itad_deals(steam_app_id),
                self._wishlist_reader.is_in_wishlist(uid, game_id),
                return_exceptions=True,
            )
            steam = _ok(results[0], None)
            protondb = _ok(results[1], None)
            hltb = _ok(results[2], None)
            deals: list[Deal] = _ok(results[3], [])
            is_in_wishlist: bool = _ok(results[4], False)
        else:
            steam = None
            protondb = None
            hltb = None
            deals = []
            is_in_wishlist = False

        # ------------------------------------------------------------------
        # Phase 3 — Assemble
        # ------------------------------------------------------------------
        return GameDetail(
            game_id=game_id,
            title=title,
            steam_app_id=steam_app_id,
            steam=steam,
            protondb=protondb,
            hltb=hltb,
            deals=deals,
            is_in_wishlist=is_in_wishlist,
        )

    async def _get_itad_deals(self, steam_app_id: int) -> list[Deal]:
        """Resolve ITAD UUID from steam_app_id and fetch current deals."""
        itad_id = await self._itad.lookup_game_id_by_steam_app_id(str(steam_app_id))
        if itad_id is None:
            return []
        return await self._itad.get_prices_for_game(itad_id)
