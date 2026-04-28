"""Get wishlist use case with ITAD deal enrichment."""

import logging
from typing import Any

from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from modules.wishlist.domain.entities.wishlist_item import WishlistItem
from modules.wishlist.domain.interfaces.repositories.i_wishlist_repository import (
    IWishlistRepository,
)
from modules.wishlist.domain.interfaces.use_cases.get_wishlist import IGetWishlistUseCase
from shared.config import get_settings
from shared.domain.interfaces.itad_client import IItadClient

logger = logging.getLogger(__name__)


class GetWishlistUseCase(IGetWishlistUseCase):
    """Fetch wishlist items and enrich each with current ITAD deals."""

    def __init__(
        self,
        repo: IWishlistRepository,
        itad_client: IItadClient,
        settings_repo: ISettingsRepository | None = None,
    ) -> None:
        self._repo = repo
        self._itad = itad_client
        self._settings_repo = settings_repo

    async def execute(
        self, uid: str, country: str | None = None
    ) -> list[tuple[WishlistItem, list[Any]]]:
        items = await self._repo.get_items(uid)
        if not items:
            return []

        effective_country = await self._resolve_country(uid, country)

        # Batch resolve ITAD game IDs for all titles
        titles = [item.title for item in items]
        try:
            title_to_itad_id = await self._itad.lookup_game_ids_batch(titles)
        except Exception:
            logger.warning("ITAD batch ID lookup failed; skipping deal enrichment")
            return [(item, []) for item in items]

        itad_ids = [iid for iid in title_to_itad_id.values() if iid is not None]
        deals_by_id: dict[str, list[Any]] = {}
        if itad_ids:
            try:
                deals_by_id = await self._itad.get_prices_for_games_batch(
                    itad_ids, effective_country
                )
            except Exception:
                logger.warning("ITAD batch price lookup failed; returning empty deals")

        result: list[tuple[WishlistItem, list[Any]]] = []
        for item in items:
            itad_id = title_to_itad_id.get(item.title)
            deals: list[Any] = deals_by_id.get(itad_id, []) if itad_id else []
            result.append((item, deals))

        return result

    async def _resolve_country(self, uid: str, country: str | None) -> str:
        """Resolve effective country from param or user settings."""
        if country is not None:
            return country
        if self._settings_repo is not None:
            user_country = await self._settings_repo.get_itad_country(uid)
            if user_country is not None:
                return user_country
        return get_settings().itad_default_country
