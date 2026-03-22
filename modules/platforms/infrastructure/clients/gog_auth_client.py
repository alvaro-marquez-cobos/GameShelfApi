"""GOG OAuth2 client for authentication and game library access.

Implements ``IGogAuthClient`` using the GOG auth API and the embedded GOG
store endpoints. Tokens are exchanged using the well-known public GOG
launcher credentials (client_id and client_secret are intentionally hardcoded
as they are the publicly documented GOG OAuth client credentials).
"""

import logging
from urllib.parse import urlencode

from modules.platforms.domain.entities.gog import GogAuthToken, GogGame
from shared.config import get_settings
from shared.domain.interfaces.gog_auth_client import IGogAuthClient
from shared.infrastructure.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)

_AUTH_BASE = "https://auth.gog.com"
_EMBED_BASE = "https://embed.gog.com"
_REDIRECT_URI = "https://embed.gog.com/on_login_success?origin=client"


class GogAuthClient(IGogAuthClient):
    """Concrete GOG auth and library client.

    Args:
        client_id: GOG OAuth2 client ID. Defaults to the value in settings.
        client_secret: GOG OAuth2 client secret. Defaults to the value in settings.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        settings = get_settings()
        self._client_id = client_id or settings.gog_client_id
        self._client_secret = client_secret or settings.gog_client_secret
        self._auth_http = BaseHttpClient(base_url=_AUTH_BASE)
        self._embed_http = BaseHttpClient(base_url=_EMBED_BASE)

    async def exchange_code(self, code: str) -> GogAuthToken:
        """Exchange an authorization code for a GOG token pair."""
        response = await self._auth_http.get(
            "/token",
            params={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _REDIRECT_URI,
            },
        )
        response.raise_for_status()
        return self._parse_token(response.json())

    async def refresh_token(self, refresh_token: str) -> GogAuthToken:
        """Obtain a new GOG token pair using a refresh token."""
        response = await self._auth_http.get(
            "/token",
            params={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        response.raise_for_status()
        return self._parse_token(response.json())

    async def get_user_games(self, access_token: str) -> list[GogGame]:
        """Fetch the full game library for the authenticated GOG user."""
        games: list[GogGame] = []
        page = 1

        while True:
            response = await self._embed_http.get(
                "/account/getFilteredProducts",
                params={
                    "mediaType": 1,
                    "sortBy": "title",
                    "page": page,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": "GOG Galaxy Client",
                },
            )
            if response.status_code != 200:
                logger.warning("get_user_games page %s failed: %s", page, response.status_code)
                break

            data = response.json()
            products = data.get("products", [])
            for product in products:
                games.append(
                    GogGame(
                        id=str(product.get("id", "")),
                        title=product.get("title", ""),
                        image_url=f"https:{product['image']}_392.jpg"
                        if product.get("image")
                        else "",
                    )
                )

            total_pages = data.get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1

        return games

    def build_auth_url(self) -> str:
        """Build the GOG OAuth2 authorization URL."""
        params = {
            "client_id": self._client_id,
            "redirect_uri": _REDIRECT_URI,
            "response_type": "code",
            "layout": "client2",
        }
        return f"{_AUTH_BASE}/auth?{urlencode(params)}"

    @staticmethod
    def _parse_token(data: dict[str, object]) -> GogAuthToken:
        """Parse a raw GOG token response into a ``GogAuthToken``."""
        return GogAuthToken(
            access_token=str(data.get("access_token", "")),
            refresh_token=str(data.get("refresh_token", "")),
            user_id=str(data.get("user_id", "")),
            expires_at=str(data.get("expires_at", "")),
        )
