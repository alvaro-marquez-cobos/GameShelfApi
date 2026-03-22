"""Tests for PsnAuthClient."""

import httpx
import pytest
import respx

from modules.platforms.domain.entities.psn import PsnAuthToken, PsnGame
from modules.platforms.infrastructure.clients.psn_auth_client import (
    PsnAuthClient,
    _parse_iso8601_duration,
)

_PSN_AUTH_BASE = "https://ca.account.sony.com/api/authz/v3/oauth"


@pytest.fixture
def client() -> PsnAuthClient:
    return PsnAuthClient()


# ---------------------------------------------------------------------------
# _parse_iso8601_duration
# ---------------------------------------------------------------------------


def test_parse_duration_hours_and_minutes() -> None:
    assert _parse_iso8601_duration("PT2H30M") == 150


def test_parse_duration_minutes_only() -> None:
    assert _parse_iso8601_duration("PT45M") == 45


def test_parse_duration_hours_only() -> None:
    assert _parse_iso8601_duration("PT1H") == 60


def test_parse_duration_with_days() -> None:
    assert _parse_iso8601_duration("P1DT2H30M") == 1590


def test_parse_duration_zero() -> None:
    assert _parse_iso8601_duration("PT0S") == 0


def test_parse_duration_empty() -> None:
    assert _parse_iso8601_duration("") == 0


# ---------------------------------------------------------------------------
# exchange_npsso
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exchange_npsso_returns_token(client: PsnAuthClient) -> None:
    auth_code = "psn_auth_code_abc123"
    token_payload = {
        "access_token": "access_jwt",
        "refresh_token": "refresh_jwt",
        "account_id": "psn_user_id",
        "expires_at": "2026-01-01T00:00:00Z",
    }
    with respx.mock() as mock:
        mock.get(f"{_PSN_AUTH_BASE}/authorize").mock(
            return_value=httpx.Response(
                302,
                headers={
                    "location": f"com.scee.psxandroid.scecompcall://redirect?code={auth_code}"
                },
            )
        )
        mock.post(f"{_PSN_AUTH_BASE}/token").mock(
            return_value=httpx.Response(200, json=token_payload)
        )
        token = await client.exchange_npsso("npsso_value")

    assert isinstance(token, PsnAuthToken)
    assert token.access_token == "access_jwt"
    assert token.account_id == "psn_user_id"


@pytest.mark.asyncio
async def test_exchange_npsso_raises_when_no_code(client: PsnAuthClient) -> None:
    with respx.mock() as mock:
        mock.get(f"{_PSN_AUTH_BASE}/authorize").mock(
            return_value=httpx.Response(302, headers={"location": "com.scee://redirect"})
        )
        with pytest.raises(ValueError, match="auth code"):
            await client.exchange_npsso("bad_npsso")


# ---------------------------------------------------------------------------
# refresh_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_token_returns_new_token(client: PsnAuthClient) -> None:
    payload = {
        "access_token": "new_access",
        "refresh_token": "new_refresh",
        "account_id": "user123",
        "expires_at": "2026-06-01T00:00:00Z",
    }
    with respx.mock() as mock:
        mock.post(f"{_PSN_AUTH_BASE}/token").mock(return_value=httpx.Response(200, json=payload))
        token = await client.refresh_token("old_refresh")

    assert token.access_token == "new_access"


# ---------------------------------------------------------------------------
# get_played_games
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_played_games_returns_parsed_games(client: PsnAuthClient) -> None:
    payload = {
        "titles": [
            {
                "titleId": "CUSA12345_00",
                "name": "God of War",
                "imageList": [{"imageType": "MASTER", "url": "https://img.psn.com/gow.jpg"}],
                "playDuration": "PT15H30M",
                "firstPlayedDateTime": "2023-01-01T10:00:00Z",
                "lastPlayedDateTime": "2023-06-01T20:00:00Z",
                "category": "ps5_native_game",
            }
        ]
    }
    with respx.mock() as mock:
        mock.get("https://m.np.playstation.com/api/gamelist/v2/users/me/titles").mock(
            return_value=httpx.Response(200, json=payload)
        )
        games = await client.get_played_games("access_token")

    assert len(games) == 1
    assert isinstance(games[0], PsnGame)
    assert games[0].title_id == "CUSA12345_00"
    assert games[0].play_duration_minutes == 930
    assert games[0].image_url == "https://img.psn.com/gow.jpg"


@pytest.mark.asyncio
async def test_get_played_games_returns_empty_on_error(client: PsnAuthClient) -> None:
    with respx.mock() as mock:
        mock.get("https://m.np.playstation.com/api/gamelist/v2/users/me/titles").mock(
            return_value=httpx.Response(401)
        )
        games = await client.get_played_games("bad_token")

    assert games == []


# ---------------------------------------------------------------------------
# build_login_url
# ---------------------------------------------------------------------------


def test_build_login_url_contains_required_params(client: PsnAuthClient) -> None:
    url = client.build_login_url()
    assert "ca.account.sony.com" in url
    assert "response_type=code" in url
    assert "09515159-7237-4370-9b40-3806e67c0891" in url
