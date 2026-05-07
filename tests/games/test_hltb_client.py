"""Tests for HltbClient."""

import httpx
import pytest
import respx

from modules.games.domain.entities.hltb import HltbResult
from modules.games.infrastructure.clients.hltb_client import HltbClient

_BASE = "https://howlongtobeat.com"
_TOKEN = "test-session-token-abc123"
_TITLE = "Elden Ring"

_HP_KEY = "ign_00dedb5f"
_HP_VAL = "51d8f4cda0a3a99f"
_TOKEN_PAYLOAD = {"token": _TOKEN, "hpKey": _HP_KEY, "hpVal": _HP_VAL}
_SEARCH_PAYLOAD = {
    "data": [
        {
            "game_name": "Elden Ring",
            "comp_main": 190800,  # 53h in seconds
            "comp_plus": 252000,  # 70h in seconds
            "comp_100": 370800,  # 103h in seconds
        }
    ]
}


@pytest.fixture
def client() -> HltbClient:
    return HltbClient()


# ---------------------------------------------------------------------------
# _seconds_to_hours helper (tested through get_game_duration)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_parsed_hltb_result(client: HltbClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/api/bleed/init", params=None).mock(
            return_value=httpx.Response(200, json=_TOKEN_PAYLOAD)
        )
        mock.post("/api/bleed").mock(return_value=httpx.Response(200, json=_SEARCH_PAYLOAD))
        result = await client.get_game_duration(_TITLE)

    assert isinstance(result, HltbResult)
    assert result.main_story == 53.0
    assert result.main_extra == 70.0
    assert result.completionist == 103.0


@pytest.mark.asyncio
async def test_zero_comp_fields_return_none(client: HltbClient) -> None:
    payload = {
        "data": [{"game_name": "Test Game", "comp_main": 36000, "comp_plus": 0, "comp_100": 0}]
    }
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/api/bleed/init", params=None).mock(
            return_value=httpx.Response(200, json=_TOKEN_PAYLOAD)
        )
        mock.post("/api/bleed").mock(return_value=httpx.Response(200, json=payload))
        result = await client.get_game_duration("Test Game")

    assert result is not None
    assert result.main_story == 10.0
    assert result.main_extra is None
    assert result.completionist is None


@pytest.mark.asyncio
async def test_returns_none_when_no_results(client: HltbClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/api/bleed/init", params=None).mock(
            return_value=httpx.Response(200, json=_TOKEN_PAYLOAD)
        )
        mock.post("/api/bleed").mock(return_value=httpx.Response(200, json={"data": []}))
        result = await client.get_game_duration("Nonexistent Game XYZ")

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_token_fetch_fails(client: HltbClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/api/bleed/init", params=None).mock(return_value=httpx.Response(503))
        result = await client.get_game_duration(_TITLE)

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_token_response_has_no_token(client: HltbClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/api/bleed/init", params=None).mock(
            return_value=httpx.Response(200, json={"token": None})
        )
        result = await client.get_game_duration(_TITLE)

    assert result is None


@pytest.mark.asyncio
async def test_uses_cached_token_on_second_call(client: HltbClient) -> None:
    """Token should be reused without re-fetching if not expired."""
    with respx.mock(base_url=_BASE) as mock:
        init_route = mock.get("/api/bleed/init", params=None).mock(
            return_value=httpx.Response(200, json=_TOKEN_PAYLOAD)
        )
        mock.post("/api/bleed").mock(return_value=httpx.Response(200, json=_SEARCH_PAYLOAD))
        await client.get_game_duration(_TITLE)
        await client.get_game_duration("Another Game")

    # Token should only be fetched once
    assert init_route.call_count == 1


@pytest.mark.asyncio
async def test_refreshes_token_on_403(client: HltbClient) -> None:
    """On a 403 search response, the token is invalidated and retried once."""
    new_token_payload = {"token": "refreshed-token-xyz"}

    with respx.mock(base_url=_BASE) as mock:
        init_route = mock.get("/api/bleed/init", params=None).mock(
            side_effect=[
                httpx.Response(200, json=_TOKEN_PAYLOAD),
                httpx.Response(200, json=new_token_payload),
            ]
        )
        search_route = mock.post("/api/bleed").mock(
            side_effect=[
                httpx.Response(403),
                httpx.Response(200, json=_SEARCH_PAYLOAD),
            ]
        )
        result = await client.get_game_duration(_TITLE)

    assert isinstance(result, HltbResult)
    assert init_route.call_count == 2
    assert search_route.call_count == 2
