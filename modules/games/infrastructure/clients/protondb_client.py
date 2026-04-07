"""ProtonDB client for Linux/Proton compatibility ratings.

Implements ``IProtonDbClient`` using the undocumented ProtonDB JSON API.
Requires browser-like User-Agent and Referer headers to avoid being blocked.
Results are cached for 1 hour. Returns None gracefully when the game is not
found or the endpoint is unavailable.
"""

import logging

from modules.games.domain.entities.protondb import ProtonDbRating, to_proton_tier
from shared.domain.interfaces.protondb_client import IProtonDbClient
from shared.infrastructure.cache.decorators import cached
from shared.infrastructure.cache.keys import protondb_key
from shared.infrastructure.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)

_PROTONDB_BASE = "https://www.protondb.com"
_BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
    "Referer": "https://www.protondb.com",
    "Accept": "application/json",
}


class ProtonDbClient(IProtonDbClient):
    """Fetches ProtonDB Linux/Proton compatibility ratings for Steam games."""

    def __init__(self) -> None:
        self._http = BaseHttpClient(base_url=_PROTONDB_BASE)

    @cached(
        ttl=3600,
        key_builder=lambda self, steam_app_id: protondb_key(str(steam_app_id)),
        deserializer=lambda data: ProtonDbRating(**data) if data is not None else None,
    )
    async def get_compatibility_rating(self, steam_app_id: str) -> ProtonDbRating | None:
        """Fetch the ProtonDB rating for a Steam application (cached 1 hour)."""
        if not steam_app_id.isdigit():
            return None

        response = await self._http.get(
            f"/api/v1/reports/summaries/{steam_app_id}.json",
            headers=_BROWSER_HEADERS,
        )
        if response.status_code != 200:
            logger.warning(
                "get_compatibility_rating failed for app_id=%s status=%s",
                steam_app_id,
                response.status_code,
            )
            return None

        data = response.json()
        tier = to_proton_tier(data.get("tier"))
        trending_tier = to_proton_tier(data.get("trendingTier") or data.get("tier"))
        total = int(data.get("total") or 0)
        return ProtonDbRating(tier=tier, trending_tier=trending_tier, total=total)
