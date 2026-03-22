"""Tests for GogAuthClient."""

import httpx
import pytest
import respx

from modules.platforms.domain.entities.gog import GogAuthToken, GogGame
from modules.platforms.infrastructure.clients.gog_auth_client import GogAuthClient

_CLIENT_ID = "test-client-id"
_CLIENT_SECRET = "test-client-secret"


@pytest.fixture
def client() -> GogAuthClient:
    return GogAuthClient(client_id=_CLIENT_ID, client_secret=_CLIENT_SECRET)


# ---------------------------------------------------------------------------
# exchange_code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exchange_code_returns_token(client: GogAuthClient) -> None:
    payload = {
        "access_token": "access123",
        "refresh_token": "refresh456",
        "user_id": "user789",
        "expires_at": "2026-01-01T00:00:00",
    }
    with respx.mock(base_url="https://auth.gog.com") as mock:
        mock.get("/token").mock(return_value=httpx.Response(200, json=payload))
        token = await client.exchange_code("authcode")

    assert isinstance(token, GogAuthToken)
    assert token.access_token == "access123"
    assert token.user_id == "user789"


@pytest.mark.asyncio
async def test_exchange_code_raises_on_error(client: GogAuthClient) -> None:
    with respx.mock(base_url="https://auth.gog.com") as mock:
        mock.get("/token").mock(return_value=httpx.Response(401))
        with pytest.raises(httpx.HTTPStatusError):
            await client.exchange_code("bad-code")


# ---------------------------------------------------------------------------
# refresh_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_token_returns_new_token(client: GogAuthClient) -> None:
    payload = {
        "access_token": "new_access",
        "refresh_token": "new_refresh",
        "user_id": "user789",
        "expires_at": "2026-06-01T00:00:00",
    }
    with respx.mock(base_url="https://auth.gog.com") as mock:
        mock.get("/token").mock(return_value=httpx.Response(200, json=payload))
        token = await client.refresh_token("old_refresh")

    assert token.access_token == "new_access"
    assert token.refresh_token == "new_refresh"


# ---------------------------------------------------------------------------
# get_user_games
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_games_single_page(client: GogAuthClient) -> None:
    payload = {
        "products": [
            {"id": 1234567890, "title": "The Witcher 3", "image": "/path/to/image"},
        ],
        "totalPages": 1,
    }
    with respx.mock(base_url="https://embed.gog.com") as mock:
        mock.get("/account/getFilteredProducts").mock(
            return_value=httpx.Response(200, json=payload)
        )
        games = await client.get_user_games("access_token")

    assert len(games) == 1
    assert isinstance(games[0], GogGame)
    assert games[0].title == "The Witcher 3"
    assert games[0].id == "1234567890"


@pytest.mark.asyncio
async def test_get_user_games_multi_page(client: GogAuthClient) -> None:
    page1 = {
        "products": [{"id": 111, "title": "Game A", "image": ""}],
        "totalPages": 2,
    }
    page2 = {
        "products": [{"id": 222, "title": "Game B", "image": ""}],
        "totalPages": 2,
    }
    with respx.mock(base_url="https://embed.gog.com") as mock:
        mock.get("/account/getFilteredProducts").mock(
            side_effect=[
                httpx.Response(200, json=page1),
                httpx.Response(200, json=page2),
            ]
        )
        games = await client.get_user_games("access_token")

    assert len(games) == 2
    assert games[0].title == "Game A"
    assert games[1].title == "Game B"


@pytest.mark.asyncio
async def test_get_user_games_returns_empty_on_error(client: GogAuthClient) -> None:
    with respx.mock(base_url="https://embed.gog.com") as mock:
        mock.get("/account/getFilteredProducts").mock(return_value=httpx.Response(401))
        games = await client.get_user_games("bad_token")

    assert games == []


# ---------------------------------------------------------------------------
# build_auth_url
# ---------------------------------------------------------------------------


def test_build_auth_url_contains_required_params(client: GogAuthClient) -> None:
    url = client.build_auth_url()
    assert "auth.gog.com/auth" in url
    assert "response_type=code" in url
    assert "client_id=" in url
