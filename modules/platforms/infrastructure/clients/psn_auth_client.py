"""PlayStation Network OAuth2 client for authentication and played titles.

Implements ``IPsnAuthClient`` using the PSN internal OAuth2 API. The NPSSO
exchange flow follows the same steps as the open-source psn-api library:
1. Exchange NPSSO cookie for an auth code via the authorize endpoint.
2. Exchange the auth code for access and refresh tokens.

ISO 8601 play durations (e.g. "PT2H30M") are converted to total minutes.
Rate limit is 300 requests per 15 minutes.
"""

import logging
import re
from urllib.parse import parse_qs, urlencode, urlparse

from modules.platforms.domain.entities.psn import PsnAuthToken, PsnGame
from shared.domain.interfaces.psn_auth_client import IPsnAuthClient
from shared.infrastructure.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)

_PSN_AUTH_BASE = "https://ca.account.sony.com/api/authz/v3/oauth"
_PSN_TITLES_URL = (
    "https://m.np.playstation.com/api/gamelist/v2/users/me/titles"
    "?categories=ps4_game,ps5_native_game&limit=200&offset=0"
)
_PSN_CLIENT_ID = "09515159-7237-4370-9b40-3806e67c0891"
_PSN_REDIRECT_URI = "com.scee.psxandroid.scecompcall://redirect"
_PSN_SCOPE = "psn:mobile.v2.core psn:clientapp"


def _parse_iso8601_duration(duration: str) -> int:
    """Parse an ISO 8601 duration string to total minutes.

    Supports the subset used by PSN: P[nD]T[nH][nM][nS].

    Args:
        duration: ISO 8601 duration string (e.g. "PT2H30M", "P1DT3H").

    Returns:
        Total duration in minutes (fractional seconds are ignored).
    """
    pattern = r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:\d+S)?"
    match = re.match(pattern, duration or "")
    if not match:
        return 0
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    return days * 24 * 60 + hours * 60 + minutes


class PsnAuthClient(IPsnAuthClient):
    """Concrete PSN auth and played-titles client."""

    def __init__(self) -> None:
        self._auth_http = BaseHttpClient(
            base_url=_PSN_AUTH_BASE,
            max_retries=2,
        )
        self._api_http = BaseHttpClient(max_retries=2)

    async def exchange_npsso(self, npsso_code: str) -> PsnAuthToken:
        """Exchange an NPSSO cookie value for a PSN token pair.

        Step 1: Use the NPSSO as a cookie to get an auth code.
        Step 2: Exchange the auth code for access/refresh tokens.
        """
        auth_code = await self._get_auth_code(npsso_code)
        return await self._exchange_code_for_tokens(auth_code)

    async def refresh_token(self, refresh_token: str) -> PsnAuthToken:
        """Obtain a new PSN token pair using a refresh token."""
        response = await self._auth_http.post(
            "/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": _PSN_CLIENT_ID,
                "token_format": "jwt",
            },
        )
        response.raise_for_status()
        return self._parse_token(response.json())

    async def get_played_games(self, access_token: str) -> list[PsnGame]:
        """Fetch the list of played titles for the authenticated PSN user."""
        response = await self._api_http.get(
            _PSN_TITLES_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            logger.warning("get_played_games failed with status %s", response.status_code)
            return []

        titles = response.json().get("titles", [])
        games: list[PsnGame] = []
        for title in titles:
            image_url = ""
            for img in title.get("imageList", []):
                if img.get("imageType") == "MASTER":
                    image_url = img.get("url", "")
                    break

            duration_str = title.get("playDuration", "PT0S")
            games.append(
                PsnGame(
                    title_id=title.get("titleId", ""),
                    name=title.get("name", ""),
                    image_url=image_url,
                    play_duration_minutes=_parse_iso8601_duration(duration_str),
                    first_played_at=title.get("firstPlayedDateTime", ""),
                    last_played_at=title.get("lastPlayedDateTime", ""),
                    platform=title.get("category", ""),
                )
            )
        return games

    def build_login_url(self) -> str:
        """Build the PSN OAuth2 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": _PSN_CLIENT_ID,
            "redirect_uri": _PSN_REDIRECT_URI,
            "scope": _PSN_SCOPE,
            "access_type": "offline",
        }
        return f"{_PSN_AUTH_BASE}/authorize?{urlencode(params)}"

    async def _get_auth_code(self, npsso_code: str) -> str:
        """Use the NPSSO cookie to obtain a PSN authorization code."""
        params = {
            "response_type": "code",
            "client_id": _PSN_CLIENT_ID,
            "redirect_uri": _PSN_REDIRECT_URI,
            "scope": _PSN_SCOPE,
            "access_type": "offline",
        }
        response = await self._auth_http.get(
            "/authorize",
            params=params,
            headers={"Cookie": f"npsso={npsso_code}"},
            follow_redirects=False,
        )
        location = response.headers.get("location", "")
        code_values = parse_qs(urlparse(location).query).get("code", [])
        if not code_values:
            raise ValueError("PSN NPSSO exchange did not return an auth code")
        return str(code_values[0])

    async def _exchange_code_for_tokens(self, code: str) -> PsnAuthToken:
        """Exchange a PSN authorization code for access and refresh tokens."""
        response = await self._auth_http.post(
            "/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _PSN_REDIRECT_URI,
                "client_id": _PSN_CLIENT_ID,
                "token_format": "jwt",
            },
        )
        response.raise_for_status()
        return self._parse_token(response.json())

    @staticmethod
    def _parse_token(data: dict[str, object]) -> PsnAuthToken:
        """Parse a raw PSN token response into a ``PsnAuthToken``."""
        return PsnAuthToken(
            access_token=str(data.get("access_token", "")),
            refresh_token=str(data.get("refresh_token", "")),
            account_id=str(data.get("account_id", "")),
            expires_at=str(data.get("expires_at", "")),
        )
