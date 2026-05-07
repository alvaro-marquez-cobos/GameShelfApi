"""HowLongToBeat client for game completion time data.

Implements ``IHltbClient`` using the internal (undocumented) HLTB API:

  1. GET /api/bleed/init?t={timestamp} — Obtain a short-lived session token
     plus honeypot key/value pair (hpKey, hpVal).
  2. POST /api/bleed with headers ``x-auth-token``, ``x-hp-key``, ``x-hp-val``
     and the honeypot field injected into the request body — Search for game data.

The session credentials are cached for 25 minutes and refreshed automatically
on 403 responses. Game duration data is cached for 1 hour. Duration fields
from the API are in seconds and are converted to hours (rounded to 1 decimal
place).

Browser-like headers (User-Agent, Referer, Origin) are required to avoid
being blocked by the HLTB server.
"""

import logging
import time
from dataclasses import dataclass

from modules.games.domain.entities.hltb import HltbResult
from shared.domain.interfaces.hltb_client import IHltbClient
from shared.infrastructure.cache.decorators import cached
from shared.infrastructure.cache.keys import hltb_key
from shared.infrastructure.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)

_HLTB_BASE = "https://howlongtobeat.com"
_HLTB_TOKEN_TTL = 25 * 60  # 25 minutes in seconds
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://howlongtobeat.com",
    "Origin": "https://howlongtobeat.com",
}

_TOP_N_RESULTS = 5


@dataclass
class _SessionCreds:
    token: str
    hp_key: str | None
    hp_val: str | None


def _seconds_to_hours(seconds: int) -> float | None:
    """Convert seconds to hours rounded to 1 decimal place, or None if zero."""
    if seconds <= 0:
        return None
    return round(seconds / 3600, 1)


class HltbClient(IHltbClient):
    """Fetches game completion time data from HowLongToBeat."""

    def __init__(self) -> None:
        self._http = BaseHttpClient(base_url=_HLTB_BASE)
        self._cached_creds: _SessionCreds | None = None
        self._creds_expires_at: float = 0.0

    @cached(
        ttl=3600,
        key_builder=lambda self, game_title: hltb_key(game_title.lower().strip()),
        deserializer=lambda data: HltbResult(**data) if data is not None else None,
    )
    async def get_game_duration(self, game_title: str) -> HltbResult | None:
        """Fetch completion time data for a game by title (cached 1 hour)."""
        try:
            creds = await self._fetch_creds()
            if not creds:
                return None
            return await self._search(game_title, creds)
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 403:
                self._cached_creds = None
                try:
                    fresh_creds = await self._fetch_creds()
                    if not fresh_creds:
                        return None
                    return await self._search(game_title, fresh_creds)
                except Exception:
                    return None
            logger.warning("get_game_duration failed for title=%r: %s", game_title, exc)
            return None

    async def _fetch_creds(self) -> _SessionCreds | None:
        """Return valid HLTB session credentials, refreshing them if expired."""
        if self._cached_creds and time.monotonic() < self._creds_expires_at:
            return self._cached_creds

        response = await self._http.get(
            f"/api/bleed/init?t={int(time.time() * 1000)}",
            headers=_BROWSER_HEADERS,
        )
        if response.status_code != 200:
            logger.warning("_fetch_creds failed with status %s", response.status_code)
            return None

        payload = response.json()
        token: str | None = payload.get("token")
        if not token:
            return None

        creds = _SessionCreds(
            token=token,
            hp_key=payload.get("hpKey"),
            hp_val=payload.get("hpVal"),
        )
        self._cached_creds = creds
        self._creds_expires_at = time.monotonic() + _HLTB_TOKEN_TTL
        return creds

    async def _search(self, game_title: str, creds: _SessionCreds) -> HltbResult | None:
        """POST the search request and parse the first result."""
        body: dict = {
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
        if creds.hp_key:
            body[creds.hp_key] = creds.hp_val

        response = await self._http.post(
            "/api/bleed",
            json=body,
            headers={
                "Content-Type": "application/json",
                "x-auth-token": creds.token,
                "x-hp-key": creds.hp_key or "",
                "x-hp-val": creds.hp_val or "",
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
