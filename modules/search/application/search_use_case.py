"""Search games use case."""

import asyncio
import logging

from modules.search.domain.entities.search_result import SearchResult
from modules.search.domain.interfaces.use_cases.search_games import ISearchGamesUseCase
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.i_game_reader import IGameReader
from shared.domain.interfaces.i_wishlist_reader import IWishlistReader
from shared.domain.interfaces.itad_client import IItadClient

logger = logging.getLogger(__name__)


class SearchGamesUseCase(ISearchGamesUseCase):
    """Search ITAD and cross-reference results with user's library and wishlist."""

    def __init__(
        self,
        itad_client: IItadClient,
        game_reader: IGameReader,
        wishlist_reader: IWishlistReader,
    ) -> None:
        self._itad = itad_client
        self._game_reader = game_reader
        self._wishlist_reader = wishlist_reader

    async def execute(self, uid: str, query: str) -> list[SearchResult]:
        try:
            itad_results = await self._itad.search_games(query)
        except Exception:
            logger.warning("ITAD search failed for query '%s'", query)
            return []

        if not itad_results:
            return []

        # Filter out non-base-games (DLCs, bundles, etc.) — keep only base games.
        itad_results = [r for r in itad_results if not r.game_type or r.game_type == "game"]

        if not itad_results:
            return []

        # Filter out non-base-games: soundtracks, OSTs, special editions (Deluxe, GOTY, etc.).
        _EXCLUDED_PATTERNS = ("soundtrack", "ost", "deluxe", "goty", "edition")
        itad_results = [
            r
            for r in itad_results
            if not any(pattern in r.title.lower() for pattern in _EXCLUDED_PATTERNS)
        ]

        if not itad_results:
            return []

        itad_results = itad_results[:5]

        steam_game_ids = {
            f"steam_{item.steam_app_id}" for item in itad_results if item.steam_app_id
        }
        itad_ids = {item.id for item in itad_results}

        owned_ids, wishlist_ids = await asyncio.gather(
            self._game_reader.check_owned_game_ids(uid, steam_game_ids),
            self._wishlist_reader.check_wishlist_ids(uid, itad_ids),
            return_exceptions=True,
        )

        if isinstance(owned_ids, BaseException):
            logger.warning("Failed to fetch owned game IDs")
            owned_ids = set()
        if isinstance(wishlist_ids, BaseException):
            logger.warning("Failed to fetch wishlist IDs")
            wishlist_ids = set()

        results: list[SearchResult] = []
        for item in itad_results:
            steam_game_id = f"steam_{item.steam_app_id}" if item.steam_app_id else None
            owned_platforms: list[Platform] = []
            if steam_game_id and steam_game_id in owned_ids:
                owned_platforms.append(Platform.STEAM)
            results.append(
                SearchResult(
                    id=item.id,
                    title=item.title,
                    cover_url=item.cover_url,
                    steam_app_id=item.steam_app_id,
                    game_type=item.game_type,
                    is_owned=bool(owned_platforms),
                    owned_platforms=owned_platforms,
                    is_in_wishlist=item.id in wishlist_ids,
                )
            )

        return results
