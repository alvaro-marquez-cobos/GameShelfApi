"""Steam Web API client for authentication and player library data.

Implements ``ISteamAuthClient`` using the Steam Web API (OpenID 2.0 auth and
IPlayerService / ISteamUser endpoints). A shared asyncio semaphore limits
concurrent calls to ``steam_max_concurrent`` (default: 3) across both this
client and ``SteamMetadataClient``.
"""

import logging
import re
from urllib.parse import urlencode

from modules.platforms.domain.entities.steam import SteamGame, SteamPlayer
from shared.config import get_settings
from shared.domain.interfaces.steam_auth_client import ISteamAuthClient
from shared.infrastructure.http.base_client import BaseHttpClient
from shared.infrastructure.http.steam_semaphore import steam_semaphore

logger = logging.getLogger(__name__)

_STEAM_API_BASE = "https://api.steampowered.com"
_STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
_STEAM_OPENID_NS = "http://specs.openid.net/auth/2.0"


class SteamAuthClient(ISteamAuthClient):
    """Concrete Steam Web API client.

    Args:
        api_key: Steam Web API developer key. Defaults to the value in settings.
    """

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.steam_api_key
        self._http = BaseHttpClient(base_url=_STEAM_API_BASE)

    async def get_owned_games(self, steam_id: str) -> list[SteamGame]:
        """Return the full list of owned games for a Steam user."""
        async with steam_semaphore:
            response = await self._http.get(
                "/IPlayerService/GetOwnedGames/v1/",
                params={
                    "key": self._api_key,
                    "steamid": steam_id,
                    "include_appinfo": 1,
                    "include_played_free_games": 1,
                    "skip_unvetted_apps": "false",
                    "format": "json",
                },
            )
        if response.status_code != 200:
            logger.warning("get_owned_games failed with status %s", response.status_code)
            return []

        data = response.json().get("response", {})
        return [self._parse_game(g) for g in data.get("games", [])]

    async def get_recently_played(self, steam_id: str) -> list[SteamGame]:
        """Return games played in the last two weeks for a Steam user."""
        async with steam_semaphore:
            response = await self._http.get(
                "/IPlayerService/GetRecentlyPlayedGames/v1/",
                params={
                    "key": self._api_key,
                    "steamid": steam_id,
                    "format": "json",
                },
            )
        if response.status_code != 200:
            logger.warning("get_recently_played failed with status %s", response.status_code)
            return []

        data = response.json().get("response", {})
        return [self._parse_game(g) for g in data.get("games", [])]

    async def get_most_played_global(self, limit: int = 100) -> list[SteamGame]:
        """Return the global most-played games chart."""
        async with steam_semaphore:
            response = await self._http.get(
                "/ISteamChartsService/GetMostPlayedGames/v1/",
                params={"key": self._api_key, "format": "json"},
            )
        if response.status_code != 200:
            logger.warning("get_most_played_global failed with status %s", response.status_code)
            return []

        ranks = response.json().get("response", {}).get("ranks", [])
        return [
            SteamGame(app_id=entry["appid"], name=entry.get("appid", ""), playtime_forever=0)
            for entry in ranks[:limit]
            if "appid" in entry
        ]

    async def get_player_summary(self, steam_id: str) -> SteamPlayer | None:
        """Return profile information for a Steam user."""
        async with steam_semaphore:
            response = await self._http.get(
                "/ISteamUser/GetPlayerSummaries/v2/",
                params={
                    "key": self._api_key,
                    "steamids": steam_id,
                    "format": "json",
                },
            )
        if response.status_code != 200:
            logger.warning("get_player_summary failed with status %s", response.status_code)
            return None

        players = response.json().get("response", {}).get("players", [])
        if not players:
            return None

        p = players[0]
        return SteamPlayer(
            steam_id=p.get("steamid", steam_id),
            persona_name=p.get("personaname", ""),
            avatar_url=p.get("avatarfull", p.get("avatar", "")),
            profile_url=p.get("profileurl", ""),
            last_logoff=p.get("lastlogoff", 0),
        )

    async def resolve_vanity_url(self, vanity: str) -> str | None:
        """Resolve a Steam vanity URL to a SteamID64 string."""
        async with steam_semaphore:
            response = await self._http.get(
                "/ISteamUser/ResolveVanityURL/v1/",
                params={
                    "key": self._api_key,
                    "vanityurl": vanity,
                    "format": "json",
                },
            )
        if response.status_code != 200:
            return None

        result = response.json().get("response", {})
        if result.get("success") != 1:
            return None
        return str(result.get("steamid", "")) or None

    def build_openid_url(self, return_url: str) -> str:
        """Build the Steam OpenID 2.0 authentication URL."""
        params = {
            "openid.ns": _STEAM_OPENID_NS,
            "openid.mode": "checkid_setup",
            "openid.return_to": return_url,
            "openid.realm": return_url,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
        return f"{_STEAM_OPENID_URL}?{urlencode(params)}"

    async def verify_openid(self, params: dict[str, str]) -> str | None:
        """Verify an OpenID callback and return the authenticated SteamID64."""
        verify_params = {**params, "openid.mode": "check_authentication"}
        async with steam_semaphore:
            response = await self._http.post(
                _STEAM_OPENID_URL,
                data=verify_params,
            )
        if response.status_code != 200:
            return None

        if "is_valid:true" not in response.text:
            return None

        claimed_id = params.get("openid.claimed_id", "")
        match = re.search(r"/id/(\d+)$", claimed_id)
        if not match:
            return None
        return match.group(1)

    @staticmethod
    def _parse_game(raw: dict) -> SteamGame:  # type: ignore[type-arg]
        """Parse a raw Steam game JSON object into a ``SteamGame``."""
        return SteamGame(
            app_id=raw.get("appid", 0),
            name=raw.get("name", ""),
            playtime_forever=raw.get("playtime_forever", 0),
            playtime_2weeks=raw.get("playtime_2weeks", 0),
            img_icon_url=raw.get("img_icon_url", ""),
            header_image=raw.get("header_image", ""),
            last_played=raw.get("rtime_last_played", 0),
        )
