"""IsThereAnyDeal client for game price and metadata lookups.

Implements ``IItadClient`` using the ITAD v2 official API.
Authentication uses an API key passed as the ``key`` query parameter.

Recommended lookup flow for deals:
  1. ``lookup_game_id_by_steam_app_id()`` — if available (may be deprecated).
  2. ``search_games()`` — title search to find UUID with matching Steam App ID (fallback).
  3. ``get_prices_for_game()`` — with the ITAD UUID from step 1 or 2.

``get_game_info()`` results are cached for 1 hour. All other methods return
live data on every call to ensure price accuracy.
"""

import logging
import re
from typing import Any

from modules.games.domain.entities.itad import Deal, ItadGameInfo, ItadSearchResult
from shared.config import get_settings
from shared.domain.interfaces.itad_client import IItadClient
from shared.infrastructure.cache.decorators import cached
from shared.infrastructure.cache.keys import itad_info_key
from shared.infrastructure.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)

_ITAD_BASE = "https://api.isthereanydeal.com"
_ENRICH_TOP_N = 5


class ItadClient(IItadClient):
    """Fetches game prices and metadata from IsThereAnyDeal."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.itad_api_key
        self._http = BaseHttpClient(base_url=_ITAD_BASE)

    @property
    def _auth(self) -> dict[str, str]:
        return {"key": self._api_key}

    async def lookup_game_id(self, title: str) -> str | None:
        """Resolve a game title to an ITAD UUID."""
        try:
            response = await self._http.get(
                "/games/lookup/v1",
                params={**self._auth, "title": title},
            )
            logger.debug(
                "ITAD lookup_game_id title=%r status=%s body=%s",
                title,
                response.status_code,
                response.text[:500],
            )
            if response.status_code != 200:
                return None
            data = response.json() or {}
            if data.get("found") and data.get("game", {}).get("id"):
                return str(data["game"]["id"])
            return None
        except Exception:
            return None

    async def lookup_game_ids_batch(self, titles: list[str]) -> dict[str, str | None]:
        """Resolve multiple titles to ITAD UUIDs, one request per title."""
        result_map: dict[str, str | None] = {t: None for t in titles}
        if not titles:
            return result_map
        import asyncio as _asyncio

        lookups = [self.lookup_game_id(t) for t in titles]
        results = await _asyncio.gather(*lookups, return_exceptions=True)
        for title, res in zip(titles, results, strict=False):
            result_map[title] = res if isinstance(res, str) else None
        return result_map

    async def lookup_game_id_by_steam_app_id(self, steam_app_id: str) -> str | None:
        """Resolve a Steam app ID to an ITAD UUID.

        The /games/lookup/id/shop/v1 endpoint no longer exists in the ITAD API.
        This method always returns None — callers should use lookup_game_id(title) instead.
        """
        return None

    async def get_prices_for_game(self, itad_game_id: str, country: str) -> list[Deal]:
        """Fetch current store deals for a game."""
        try:
            response = await self._http.post(
                "/games/prices/v2",
                json=[itad_game_id],
                params={**self._auth, "country": country},
            )
            logger.debug(
                "ITAD get_prices_for_game id=%s status=%s body=%s",
                itad_game_id,
                response.status_code,
                response.text[:500],
            )
            if response.status_code != 200:
                return []
            results = response.json() or []
            deals_raw = results[0].get("deals", []) if results else []
            logger.debug("ITAD get_prices_for_game id=%s -> %d deals", itad_game_id, len(deals_raw))
            return [self._map_deal(d, i) for i, d in enumerate(deals_raw)]
        except Exception:
            return []

    async def get_prices_for_games_batch(
        self, itad_game_ids: list[str], country: str
    ) -> dict[str, list[Deal]]:
        """Fetch current deals for multiple games in a single request."""
        result_map: dict[str, list[Deal]] = {gid: [] for gid in itad_game_ids}
        if not itad_game_ids:
            return result_map
        try:
            response = await self._http.post(
                "/games/prices/v2",
                json=itad_game_ids,
                params={**self._auth, "country": country},
            )
            if response.status_code != 200:
                return result_map
            entries = response.json() or []
            for game_id, entry in zip(itad_game_ids, entries, strict=False):
                deals_raw = entry.get("deals", []) if entry else []
                result_map[game_id] = [self._map_deal(d, i) for i, d in enumerate(deals_raw)]
        except Exception:
            pass
        return result_map

    async def get_historical_low(self, itad_game_id: str, country: str) -> Deal | None:
        """Fetch the all-time historical low price for a game."""
        try:
            response = await self._http.post(
                "/games/historylow/v1",
                json=[itad_game_id],
                params={**self._auth, "country": country},
            )
            if response.status_code != 200:
                return None
            results = response.json() or []
            low = results[0] if results else None
            if not low:
                return None
            return Deal(
                id=f"histlow_{itad_game_id}",
                store_name=low.get("shop", {}).get("name", "Unknown"),
                price=float(low.get("price", {}).get("amount", 0)),
                regular_price=float(low.get("regular", {}).get("amount", 0)),
                discount=int(low.get("cut", 0)),
                url=str(low.get("url", "")),
                currency=str(low.get("price", {}).get("currency", "USD")),
            )
        except Exception:
            return None

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Remove trademark symbols, registered symbols, and superscript characters."""
        cleaned = re.sub(r"[™®\uFE0F]", "", query)
        cleaned = re.sub(
            r"[\u00B9\u2070\u2071\u2074-\u2079\u2080-\u2089"
            r"\u207A\u207B\u207C\u207D\u207E"
            r"\u207F]",
            "",
            cleaned,
        )
        return re.sub(r"\s+", " ", cleaned).strip()

    async def search_games(self, query: str) -> list[ItadSearchResult]:
        """Search for games by title and enrich the top 5 with Steam app IDs."""
        try:
            sanitized = self._sanitize_query(query)
            response = await self._http.get(
                "/games/search/v1",
                params={**self._auth, "title": sanitized, "limit": 20},
            )
            if response.status_code != 200:
                return []

            raw_results = response.json() or []
            results = [
                ItadSearchResult(
                    id=r["id"],
                    title=r.get("title", ""),
                    cover_url=(
                        r.get("assets", {}).get("banner300")
                        or r.get("assets", {}).get("banner400")
                        or ""
                    ),
                    steam_app_id=None,
                    game_type=r.get("type"),
                )
                for r in raw_results
            ]

            top = results[:_ENRICH_TOP_N]
            rest = results[_ENRICH_TOP_N:]

            enriched: list[ItadSearchResult] = []
            for r in top:
                info = await self.get_game_info(r.id)
                if info and info.steam_app_id is not None:
                    enriched.append(
                        ItadSearchResult(
                            id=r.id,
                            title=r.title,
                            cover_url=r.cover_url,
                            steam_app_id=info.steam_app_id,
                            game_type=r.game_type,
                        )
                    )
                else:
                    enriched.append(r)

            return enriched + rest
        except Exception:
            return []

    @cached(
        ttl=3600,
        key_builder=lambda self, itad_game_id: itad_info_key(itad_game_id),
        deserializer=lambda data: ItadGameInfo(**data) if data is not None else None,
    )
    async def get_game_info(self, itad_game_id: str) -> ItadGameInfo | None:
        """Fetch metadata for a game from ITAD (cached 1 hour)."""
        try:
            response = await self._http.get(
                "/games/info/v2",
                params={**self._auth, "id": itad_game_id},
            )
            if response.status_code != 200:
                return None
            data = response.json() or {}
            assets = data.get("assets") or {}
            return ItadGameInfo(
                id=str(data.get("id", "")),
                title=str(data.get("title", "")),
                steam_app_id=int(data["appid"]) if data.get("appid") else None,
                cover_url=str(assets.get("banner300") or assets.get("banner400") or ""),
            )
        except Exception:
            return None

    @staticmethod
    def _map_deal(entry: dict[str, Any], index: int) -> Deal:
        """Parse a raw ITAD price entry into a ``Deal``."""
        shop = entry.get("shop") or {}
        price = entry.get("price") or {}
        regular = entry.get("regular") or {}
        return Deal(
            id=f"{shop.get('id', '')}_{index}",
            store_name=str(shop.get("name", "")),
            price=float(price.get("amount") or 0),
            regular_price=float(regular.get("amount") or 0),
            discount=int(entry.get("cut") or 0),
            url=str(entry.get("url", "")),
            currency=str(price.get("currency") or "USD"),
        )
