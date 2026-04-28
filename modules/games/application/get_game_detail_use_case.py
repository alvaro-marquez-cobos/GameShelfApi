"""Get game detail use case — 3-phase enrichment."""

import asyncio
import contextlib
import logging
from typing import Any

from modules.games.domain.entities.game_detail import GameDetail
from modules.games.domain.entities.itad import Deal
from modules.games.domain.interfaces.repositories.i_game_repository import IGameRepository
from modules.games.domain.interfaces.use_cases.get_game_detail import IGetGameDetailUseCase
from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from shared.config import get_settings
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.hltb_client import IHltbClient
from shared.domain.interfaces.i_library_reader import ILibraryReader
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

    Phase 1 — Resolve title and Steam app ID (library entry first, then
               the games metadata cache, then deterministic game_id parsing,
               then Steam store search by title).
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
        library_reader: ILibraryReader,
        settings_repo: ISettingsRepository | None = None,
    ) -> None:
        self._repo = repo
        self._steam_metadata = steam_metadata
        self._protondb = protondb
        self._hltb = hltb
        self._itad = itad
        self._wishlist_reader = wishlist_reader
        self._library_reader = library_reader
        self._settings_repo = settings_repo

    async def execute(
        self,
        uid: str,
        game_id: str,
        platform: Platform | None = None,
        steam_app_id_hint: int | None = None,
        country: str | None = None,
    ) -> GameDetail:
        # ------------------------------------------------------------------
        # Phase 1 — Resolve title and Steam app ID from user's library first,
        # then fall back to the shared games metadata collection.
        # ------------------------------------------------------------------
        library_game = await self._library_reader.get_game(uid, game_id)
        title = library_game.title if library_game and library_game.title else game_id
        steam_app_id: int | None = library_game.steam_app_id if library_game else None

        if steam_app_id is None and steam_app_id_hint is not None:
            steam_app_id = steam_app_id_hint

        if steam_app_id is None:
            game_doc = await self._repo.get_game(game_id)
            if game_doc:
                steam_app_id = game_doc.get("steam_app_id")

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
        effective_country = await self._resolve_country(uid, country)
        if steam_app_id is not None:
            results = await asyncio.gather(
                self._steam_metadata.get_app_details(steam_app_id),
                self._protondb.get_compatibility_rating(str(steam_app_id)),
                self._hltb.get_game_duration(title),
                self._get_itad_deals(steam_app_id, title, effective_country),  # Pass title for fallback
                self._wishlist_reader.is_in_wishlist(uid, game_id),
                return_exceptions=True,
            )
            steam = _ok(results[0], None)
            protondb = _ok(results[1], None)
            hltb = _ok(results[2], None)
            deals: list[Deal] = _ok(results[3], [])
            is_in_wishlist: bool = _ok(results[4], False)

            # Retry ITAD with real game name if Phase 2 used game_id as title
            # (non-library games have title=game_id before Steam resolves the name)
            if not deals and steam is not None and steam.name and steam.name != title:
                deals = await self._get_itad_deals(steam_app_id, steam.name, effective_country)
        else:
            steam = None
            protondb = None
            hltb = None
            deals = []
            is_in_wishlist = False

        # ------------------------------------------------------------------
        # Phase 3 — Assemble
        # ------------------------------------------------------------------
        # Use Steam name if available (for non-library games that resolved
        # via Steam search or game_id prefix extraction)
        if steam is not None and steam.name:
            title = steam.name

        cover_url = (
            library_game.cover_url
            if library_game
            else (steam.header_image if steam and steam.header_image else None)
        )
        portrait_cover_url = (
            f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_app_id}/library_600x900.jpg"
            if steam_app_id
            else None
        )
        playtime_minutes = library_game.playtime_minutes if library_game else 0
        last_played = library_game.last_played if library_game else None
        platform = library_game.platform if library_game else (platform or Platform.STEAM)
        description = steam.short_description if steam else ""

        return GameDetail(
            game_id=game_id,
            title=title,
            steam_app_id=steam_app_id,
            platform=platform,
            cover_url=cover_url,
            portrait_cover_url=portrait_cover_url,
            playtime_minutes=playtime_minutes,
            last_played=last_played,
            description=description,
            steam=steam,
            protondb=protondb,
            hltb=hltb,
            deals=deals,
            is_in_wishlist=is_in_wishlist,
            is_in_library=library_game is not None,
        )

    async def _resolve_country(self, uid: str, country: str | None) -> str:
        """Resolve effective country from param or user settings."""
        if country is not None:
            return country
        if self._settings_repo is not None:
            user_country = await self._settings_repo.get_itad_country(uid)
            if user_country is not None:
                return user_country
        return get_settings().itad_default_country

    async def _get_itad_deals(self, steam_app_id: int, title: str, country: str) -> list[Deal]:
        """Resolve ITAD UUID from steam_app_id and fetch current deals.

        Uses lookup by Steam App ID first, falls back to direct title lookup
        with verification if that fails.
        """
        itad_id = await self._itad.lookup_game_id_by_steam_app_id(str(steam_app_id))

        if itad_id is None:
            # Fallback: direct lookup by title (more reliable than search + enrich)
            itad_id = await self._itad.lookup_game_id(title)
            if itad_id is not None:
                # Discard only if ITAD confirms a different steam_app_id (wrong game).
                # If info is None or steam_app_id is unlinked, give the UUID
                # the benefit of the doubt.
                info = await self._itad.get_game_info(itad_id)
                if (
                    info is not None
                    and info.steam_app_id is not None
                    and info.steam_app_id != steam_app_id
                ):
                    itad_id = None

        if itad_id is None:
            return []

        return await self._itad.get_prices_for_game(itad_id, country)
