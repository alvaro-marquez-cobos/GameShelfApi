"""Epic Games OAuth2 client for authentication and game library access.

Implements ``IEpicAuthClient`` using the Epic Games launcher OAuth2 API.
Authentication uses HTTP Basic Auth with the launcherAppClient2 credentials.
Library pagination is handled via cursor. Catalog enrichment is batched at
max 50 IDs per request.
"""

import base64
import json
import logging
from urllib.parse import urlencode

from modules.platforms.domain.entities.epic import EpicAuthToken, EpicCatalogItem, EpicGame
from shared.config import get_settings
from shared.domain.interfaces.epic_auth_client import IEpicAuthClient
from shared.infrastructure.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)

_EPIC_AUTH_BASE = "https://account-public-service-prod.ol.epicgames.com"
_EPIC_LIBRARY_BASE = "https://library-service.live.use1a.on.epicgames.com"
_EPIC_CATALOG_BASE = "https://catalog-public-service-prod06.ol.epicgames.com"
_EPIC_LOGIN_URL = "https://www.epicgames.com/id/login"
_EPIC_REDIRECT_URI = "https://www.epicgames.com/id/api/redirect"

_EPIC_NON_GAME_TYPES = {
    "CONSUMABLE",
    "VIRTUAL_CURRENCY",
    "SEASON_PASS",
    "BUNDLE",
    "UNLOCKABLE",
}
_CATALOG_BATCH_SIZE = 50


class EpicAuthClient(IEpicAuthClient):
    """Concrete Epic Games auth and library client.

    Args:
        client_id: Epic OAuth2 client ID. Defaults to the value in settings.
        client_secret: Epic OAuth2 client secret. Defaults to the value in settings.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        settings = get_settings()
        self._client_id = client_id or settings.epic_client_id
        self._client_secret = client_secret or settings.epic_client_secret
        self._auth_http = BaseHttpClient(base_url=_EPIC_AUTH_BASE)
        self._library_http = BaseHttpClient(base_url=_EPIC_LIBRARY_BASE)
        self._catalog_http = BaseHttpClient(base_url=_EPIC_CATALOG_BASE)

    def _basic_auth_header(self) -> str:
        """Build the HTTP Basic Auth header value for Epic token endpoints."""
        credentials = f"{self._client_id}:{self._client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def exchange_auth_code(self, code: str) -> EpicAuthToken:
        """Exchange an authorization code for an Epic token pair."""
        response = await self._auth_http.post(
            "/account/api/oauth/token",
            data={"grant_type": "authorization_code", "code": code},
            headers={"Authorization": self._basic_auth_header()},
        )
        response.raise_for_status()
        return self._parse_token(response.json())

    async def refresh_token(self, refresh_token: str) -> EpicAuthToken:
        """Obtain a new Epic token pair using a refresh token."""
        response = await self._auth_http.post(
            "/account/api/oauth/token",
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            headers={"Authorization": self._basic_auth_header()},
        )
        response.raise_for_status()
        return self._parse_token(response.json())

    async def fetch_library(self, access_token: str, account_id: str) -> list[EpicGame]:
        """Fetch the full Epic game library, handling cursor pagination."""
        games: list[EpicGame] = []
        cursor: str | None = None

        while True:
            params: dict[str, object] = {"includeMetadata": "true"}
            if cursor:
                params["cursor"] = cursor

            response = await self._library_http.get(
                "/library/api/public/items",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                logger.warning("fetch_library failed with status %s", response.status_code)
                break

            data = response.json()
            records = data.get("records", [])
            for record in records:
                categories = [
                    c.get("name", "") for c in record.get("catalogItem", {}).get("categories", [])
                ]
                if any(c in _EPIC_NON_GAME_TYPES for c in categories):
                    continue
                games.append(
                    EpicGame(
                        app_name=record.get("appName", ""),
                        namespace=record.get("namespace", ""),
                        catalog_item_id=record.get("catalogItemId", ""),
                    )
                )

            cursor = data.get("responseMetadata", {}).get("nextCursor")
            if not cursor:
                break

        return games

    async def enrich_catalog_items(
        self,
        namespace: str,
        item_ids: list[str],
        access_token: str,
    ) -> list[EpicCatalogItem]:
        """Fetch enriched catalog metadata in batches of up to 50 IDs."""
        results: list[EpicCatalogItem] = []

        for i in range(0, len(item_ids), _CATALOG_BATCH_SIZE):
            batch = item_ids[i : i + _CATALOG_BATCH_SIZE]
            params: list[tuple[str, str]] = [("id", item_id) for item_id in batch]
            params += [
                ("locale", "en"),
                ("country", "US"),
                ("includeMainGameDetails", "true"),
            ]

            response = await self._catalog_http.get(
                f"/catalog/api/shared/namespace/{namespace}/bulk/items",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                logger.warning(
                    "enrich_catalog_items batch failed with status %s", response.status_code
                )
                continue

            for item_data in response.json().values():
                key_images = [
                    {"type": img.get("type", ""), "url": img.get("url", "")}
                    for img in item_data.get("keyImages", [])
                ]
                categories = [c.get("path", "") for c in item_data.get("categories", [])]
                results.append(
                    EpicCatalogItem(
                        id=item_data.get("id", ""),
                        title=item_data.get("title", ""),
                        description=item_data.get("description", ""),
                        key_images=key_images,
                        categories=categories,
                        developer=item_data.get("developer", ""),
                    )
                )

        return results

    def parse_gdpr_export(self, json_content: str) -> list[EpicGame]:
        """Parse an Epic GDPR data export JSON payload into game entries.

        The GDPR export contains an array of owned library records under the
        top-level key ``libraryItems`` (or as the root array itself depending
        on the export version). Non-game items are filtered out.
        """
        try:
            raw = json.loads(json_content)
        except (json.JSONDecodeError, ValueError):
            logger.warning("parse_gdpr_export received invalid JSON")
            return []

        records: list[dict[str, object]] = []
        if isinstance(raw, list):
            records = raw
        elif isinstance(raw, dict):
            records = raw.get("libraryItems", raw.get("records", []))  # type: ignore[assignment]

        games: list[EpicGame] = []
        for record in records:
            app_name = str(record.get("appName", "") or record.get("artifactId", ""))
            namespace = str(record.get("namespace", ""))
            catalog_item_id = str(record.get("catalogItemId", ""))
            if app_name:
                games.append(
                    EpicGame(
                        app_name=app_name,
                        namespace=namespace,
                        catalog_item_id=catalog_item_id,
                    )
                )
        return games

    def build_login_url(self) -> str:
        """Build the Epic Games OAuth2 authorization URL."""
        redirect_params = urlencode(
            {
                "clientId": self._client_id,
                "responseType": "code",
            }
        )
        redirect_url = f"{_EPIC_REDIRECT_URI}?{redirect_params}"
        params = urlencode({"redirectUrl": redirect_url})
        return f"{_EPIC_LOGIN_URL}?{params}"

    @staticmethod
    def _parse_token(data: dict[str, object]) -> EpicAuthToken:
        """Parse a raw Epic token response into an ``EpicAuthToken``."""
        return EpicAuthToken(
            access_token=str(data.get("access_token", "")),
            refresh_token=str(data.get("refresh_token", "")),
            account_id=str(data.get("account_id", "")),
            display_name=str(data.get("displayName", "")),
            expires_at=str(data.get("expires_at", "")),
        )
