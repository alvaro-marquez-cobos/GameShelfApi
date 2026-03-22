"""Tests for EpicAuthClient."""

import json

import httpx
import pytest
import respx

from modules.platforms.domain.entities.epic import EpicAuthToken, EpicCatalogItem, EpicGame
from modules.platforms.infrastructure.clients.epic_auth_client import EpicAuthClient

_CLIENT_ID = "test-client-id"
_CLIENT_SECRET = "test-client-secret"
_EPIC_AUTH_BASE = "https://account-public-service-prod.ol.epicgames.com"
_EPIC_LIBRARY_BASE = "https://library-service.live.use1a.on.epicgames.com"
_EPIC_CATALOG_BASE = "https://catalog-public-service-prod06.ol.epicgames.com"


@pytest.fixture
def client() -> EpicAuthClient:
    return EpicAuthClient(client_id=_CLIENT_ID, client_secret=_CLIENT_SECRET)


_TOKEN_PAYLOAD = {
    "access_token": "epic_access",
    "refresh_token": "epic_refresh",
    "account_id": "epic_user_id",
    "displayName": "EpicPlayer",
    "expires_at": "2026-01-01T00:00:00Z",
}


# ---------------------------------------------------------------------------
# exchange_auth_code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exchange_auth_code_returns_token(client: EpicAuthClient) -> None:
    with respx.mock(base_url=_EPIC_AUTH_BASE) as mock:
        mock.post("/account/api/oauth/token").mock(
            return_value=httpx.Response(200, json=_TOKEN_PAYLOAD)
        )
        token = await client.exchange_auth_code("auth_code_abc")

    assert isinstance(token, EpicAuthToken)
    assert token.access_token == "epic_access"
    assert token.account_id == "epic_user_id"
    assert token.display_name == "EpicPlayer"


@pytest.mark.asyncio
async def test_exchange_auth_code_raises_on_error(client: EpicAuthClient) -> None:
    with respx.mock(base_url=_EPIC_AUTH_BASE) as mock:
        mock.post("/account/api/oauth/token").mock(return_value=httpx.Response(401))
        with pytest.raises(httpx.HTTPStatusError):
            await client.exchange_auth_code("bad_code")


# ---------------------------------------------------------------------------
# refresh_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_token_returns_new_token(client: EpicAuthClient) -> None:
    with respx.mock(base_url=_EPIC_AUTH_BASE) as mock:
        mock.post("/account/api/oauth/token").mock(
            return_value=httpx.Response(200, json=_TOKEN_PAYLOAD)
        )
        token = await client.refresh_token("old_refresh")

    assert token.refresh_token == "epic_refresh"


# ---------------------------------------------------------------------------
# fetch_library
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_library_returns_games_and_filters_non_games(
    client: EpicAuthClient,
) -> None:
    payload = {
        "records": [
            {
                "appName": "Fortnite",
                "namespace": "fn",
                "catalogItemId": "cat1",
                "catalogItem": {"categories": []},
            },
            {
                "appName": "SomeSkin",
                "namespace": "fn",
                "catalogItemId": "cat2",
                "catalogItem": {"categories": [{"name": "CONSUMABLE"}]},
            },
        ],
        "responseMetadata": {},
    }
    with respx.mock(base_url=_EPIC_LIBRARY_BASE) as mock:
        mock.get("/library/api/public/items").mock(return_value=httpx.Response(200, json=payload))
        games = await client.fetch_library("access_token", "account_id")

    assert len(games) == 1
    assert isinstance(games[0], EpicGame)
    assert games[0].app_name == "Fortnite"


@pytest.mark.asyncio
async def test_fetch_library_handles_cursor_pagination(client: EpicAuthClient) -> None:
    def _record(app: str, item_id: str) -> dict[str, object]:
        return {
            "appName": app,
            "namespace": "ns",
            "catalogItemId": item_id,
            "catalogItem": {"categories": []},
        }

    page1 = {"records": [_record("GameA", "c1")], "responseMetadata": {"nextCursor": "cursor123"}}
    page2 = {"records": [_record("GameB", "c2")], "responseMetadata": {}}
    with respx.mock(base_url=_EPIC_LIBRARY_BASE) as mock:
        mock.get("/library/api/public/items").mock(
            side_effect=[
                httpx.Response(200, json=page1),
                httpx.Response(200, json=page2),
            ]
        )
        games = await client.fetch_library("access_token", "account_id")

    assert len(games) == 2
    assert games[0].app_name == "GameA"
    assert games[1].app_name == "GameB"


@pytest.mark.asyncio
async def test_fetch_library_returns_empty_on_error(client: EpicAuthClient) -> None:
    with respx.mock(base_url=_EPIC_LIBRARY_BASE) as mock:
        mock.get("/library/api/public/items").mock(return_value=httpx.Response(401))
        games = await client.fetch_library("bad_token", "account")

    assert games == []


# ---------------------------------------------------------------------------
# enrich_catalog_items
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enrich_catalog_items_returns_parsed_items(client: EpicAuthClient) -> None:
    catalog_response = {
        "item1": {
            "id": "item1",
            "title": "Fortnite",
            "description": "A battle royale game.",
            "keyImages": [{"type": "Thumbnail", "url": "https://img.epic.com/fn.jpg"}],
            "categories": [{"path": "games/edition/base"}],
            "developer": "Epic Games",
        }
    }
    with respx.mock(base_url=_EPIC_CATALOG_BASE) as mock:
        mock.get("/catalog/api/shared/namespace/fn/bulk/items").mock(
            return_value=httpx.Response(200, json=catalog_response)
        )
        items = await client.enrich_catalog_items("fn", ["item1"], "access_token")

    assert len(items) == 1
    assert isinstance(items[0], EpicCatalogItem)
    assert items[0].title == "Fortnite"
    assert items[0].developer == "Epic Games"


@pytest.mark.asyncio
async def test_enrich_catalog_items_batches_at_50(client: EpicAuthClient) -> None:
    item_ids = [f"id{i}" for i in range(75)]
    with respx.mock(base_url=_EPIC_CATALOG_BASE) as mock:
        route = mock.get("/catalog/api/shared/namespace/ns/bulk/items").mock(
            return_value=httpx.Response(200, json={})
        )
        await client.enrich_catalog_items("ns", item_ids, "access_token")

    assert route.call_count == 2


# ---------------------------------------------------------------------------
# parse_gdpr_export
# ---------------------------------------------------------------------------


def test_parse_gdpr_export_list_format(client: EpicAuthClient) -> None:
    records = [
        {"appName": "GameX", "namespace": "ns1", "catalogItemId": "c1"},
        {"appName": "GameY", "namespace": "ns2", "catalogItemId": "c2"},
    ]
    games = client.parse_gdpr_export(json.dumps(records))
    assert len(games) == 2
    assert games[0].app_name == "GameX"


def test_parse_gdpr_export_dict_with_library_items(client: EpicAuthClient) -> None:
    data = {"libraryItems": [{"appName": "GameZ", "namespace": "ns3", "catalogItemId": "c3"}]}
    games = client.parse_gdpr_export(json.dumps(data))
    assert len(games) == 1
    assert games[0].namespace == "ns3"


def test_parse_gdpr_export_invalid_json_returns_empty(client: EpicAuthClient) -> None:
    games = client.parse_gdpr_export("not json at all {{{")
    assert games == []


# ---------------------------------------------------------------------------
# build_login_url
# ---------------------------------------------------------------------------


def test_build_login_url_contains_required_params(client: EpicAuthClient) -> None:
    url = client.build_login_url()
    assert "epicgames.com/id/login" in url
    assert "redirectUrl=" in url
