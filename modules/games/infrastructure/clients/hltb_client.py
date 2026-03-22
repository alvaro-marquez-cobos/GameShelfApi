"""HowLongToBeat client for game completion time data.

Implements ``IHltbClient`` using the internal (undocumented) HLTB API:

  1. GET /api/finder/init?t={timestamp} — Obtain a short-lived session token.
  2. POST /api/finder with header ``x-auth-token`` — Search for game data.

The session token is cached for 25 minutes and refreshed automatically on 403
responses. Game duration data is cached for 1 hour. Duration fields from the
API are in seconds and are converted to hours (rounded to 1 decimal place).

Browser-like headers (User-Agent, Referer, Origin) are required to avoid
being blocked by the HLTB server.
"""

import logging
import time

from modules.games.domain.entities.hltb import HltbResult
from shared.domain.interfaces.hltb_client import IHltbClient
from shared.infrastructure.cache.decorators import cached
from shared.infrastructure.cache.keys import hltb_key
from shared.infrastructure.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)

_HLTB_BASE = "https://howlongtobeat.com"
_HLTB_TOKEN_TTL = 25 * 60  # 25 minutes in seconds
_BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
    "Referer": "https://howlongtobeat.com",
    "Origin": "https://howlongtobeat.com",
}

_TOP_N_RESULTS = 5


def _seconds_to_hours(seconds: int) -> float | None:
    """Convert seconds to hours rounded to 1 decimal place, or None if zero."""
    if seconds <= 0:
        return None
    return round(seconds / 3600, 1)


class HltbClient(IHltbClient):
    """Fetches game completion time data from HowLongToBeat."""

    def __init__(self) -> None:
        self._http = BaseHttpClient(base_url=_HLTB_BASE)
        self._cached_token: str | None = None
        self._token_expires_at: float = 0.0

    @cached(
        ttl=3600,
        key_builder=lambda self, game_title: hltb_key(game_title.lower().strip()),
    )
    async def get_game_duration(self, game_title: str) -> HltbResult | None:
        """Fetch completion time data for a game by title (cached 1 hour)."""
        try:
            token = await self._fetch_token()
            if not token:
                return None
            return await self._search(game_title, token)
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 403:
                self._cached_token = None
                try:
                    fresh_token = await self._fetch_token()
                    if not fresh_token:
                        return None
                    return await self._search(game_title, fresh_token)
                except Exception:
                    return None
            logger.warning("get_game_duration failed for title=%r: %s", game_title, exc)
            return None

    async def _fetch_token(self) -> str | None:
        """Return a valid HLTB session token, refreshing it if expired."""
        if self._cached_token and time.monotonic() < self._token_expires_at:
            return self._cached_token

        response = await self._http.get(
            f"/api/finder/init?t={int(time.time() * 1000)}",
            headers=_BROWSER_HEADERS,
        )
        if response.status_code != 200:
            logger.warning("_fetch_token failed with status %s", response.status_code)
            return None

        token: str | None = response.json().get("token")
        if token:
            self._cached_token = token
            self._token_expires_at = time.monotonic() + _HLTB_TOKEN_TTL
        return token

    async def _search(self, game_title: str, token: str) -> HltbResult | None:
        """POST the search request and parse the first result."""
        body = {
            "searchType": "games",
            "searchTerms": game_title.strip().split(),
            "searchPage": 1,
            "size": _TOP_N_RESULTS,
            "searchOptions": {
                "games": {
                    "userId": 0,
                    "platform": "",
                    "sortCategory": "popular",
                    "rangeCategory": "main",
                    "rangeTime": {"min": None, "max": None},
                    "gameplay": {
                        "perspective": "",
                        "flow": "",
                        "genre": "",
                        "difficulty": "",
                    },
                    "rangeYear": {"min": "", "max": ""},
                    "modifier": "",
                },
                "users": {"sortCategory": "postcount"},
                "lists": {"sortCategory": "follows"},
                "filter": "",
                "sort": 0,
                "randomizer": 0,
            },
            "useCache": True,
        }

        response = await self._http.post(
            "/api/finder",
            json=body,
            headers={
                "Content-Type": "application/json",
                "x-auth-token": token,
                **_BROWSER_HEADERS,
            },
        )
        response.raise_for_status()

        results = response.json().get("data", [])
        if not results:
            return None

        best = results[0]
        return HltbResult(
            main_story=_seconds_to_hours(int(best.get("comp_main") or 0)),
            main_extra=_seconds_to_hours(int(best.get("comp_plus") or 0)),
            completionist=_seconds_to_hours(int(best.get("comp_100") or 0)),
        )
