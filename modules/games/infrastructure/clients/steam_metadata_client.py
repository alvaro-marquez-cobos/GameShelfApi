"""Steam Store API client for game metadata.

Implements ``ISteamMetadataClient`` using the Steam Store API (appdetails and
storesearch endpoints). Shares the same ``steam_semaphore`` as
``SteamAuthClient`` to enforce the 3-concurrent-call limit globally.
"""

import logging
import re

from modules.games.domain.entities.steam import SteamAppDetails
from shared.domain.interfaces.steam_metadata_client import ISteamMetadataClient
from shared.infrastructure.cache.decorators import cached
from shared.infrastructure.cache.keys import steam_app_key
from shared.infrastructure.http.base_client import BaseHttpClient
from shared.infrastructure.http.steam_semaphore import steam_semaphore

logger = logging.getLogger(__name__)

_STORE_BASE = "https://store.steampowered.com"


def _normalize(title: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace in a title."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", title.lower())).strip()


def _word_overlap(a: str, b: str) -> float:
    """Return the word overlap ratio between two strings.

    Uses matching words divided by the max word count, matching
    the scoring strategy used in the frontend.
    """
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    matching = len(words_a & words_b)
    return matching / max(len(words_a), len(words_b))


class SteamMetadataClient(ISteamMetadataClient):
    """Fetches game metadata from the Steam Store API."""

    def __init__(self) -> None:
        self._http = BaseHttpClient(base_url=_STORE_BASE)

    @cached(ttl=3600, key_builder=lambda self, app_id: steam_app_key(app_id))
    async def get_app_details(self, app_id: int) -> SteamAppDetails | None:
        """Fetch detailed metadata for a Steam application (cached 1 hour)."""
        async with steam_semaphore:
            response = await self._http.get(
                "/api/appdetails",
                params={"appids": app_id},
            )
        if response.status_code != 200:
            logger.warning(
                "get_app_details failed for app_id=%s status=%s", app_id, response.status_code
            )
            return None

        payload = response.json().get(str(app_id), {})
        if not payload.get("success"):
            return None

        data = payload.get("data", {})
        return self._parse_app_details(app_id, data)

    async def search_store(self, title: str) -> int | None:
        """Search the Steam Store for a game by title and return its app ID."""
        async with steam_semaphore:
            response = await self._http.get(
                "/api/storesearch/",
                params={"term": title, "cc": "us", "l": "en"},
            )
        if response.status_code != 200:
            return None

        items = response.json().get("items", [])
        if not items:
            return None

        needle = _normalize(title)
        for item in items:
            candidate = _normalize(item.get("name", ""))
            if candidate == needle:
                return int(item["id"])

        for item in items:
            candidate = _normalize(item.get("name", ""))
            if needle in candidate or candidate in needle:
                return int(item["id"])

        first = items[0]
        if _word_overlap(needle, _normalize(first.get("name", ""))) >= 0.7:
            return int(first["id"])

        return None

    @staticmethod
    def _parse_app_details(app_id: int, data: dict) -> SteamAppDetails:  # type: ignore[type-arg]
        """Parse a raw Steam appdetails response into a ``SteamAppDetails``."""
        genres = [g.get("description", "") for g in data.get("genres", [])]
        screenshots = [s.get("path_full", "") for s in data.get("screenshots", [])]
        metacritic = data.get("metacritic", {})
        release = data.get("release_date", {})
        fullgame = data.get("fullgame", {})
        recommendations = data.get("recommendations", {})

        return SteamAppDetails(
            app_id=app_id,
            name=data.get("name", ""),
            short_description=data.get("short_description", ""),
            header_image=data.get("header_image", ""),
            genres=genres,
            developers=data.get("developers", []),
            publishers=data.get("publishers", []),
            release_date=release.get("date") if not release.get("coming_soon") else None,
            metacritic_score=metacritic.get("score"),
            metacritic_url=metacritic.get("url"),
            screenshots=screenshots,
            recommendation_count=recommendations.get("total"),
            app_type=data.get("type"),
            parent_steam_app_id=int(fullgame["appid"]) if fullgame.get("appid") else None,
            dlc_app_ids=data.get("dlc", []),
        )
