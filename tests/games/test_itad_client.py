"""Tests for ItadClient."""

import httpx
import pytest
import respx

from modules.games.domain.entities.itad import Deal, ItadGameInfo, ItadSearchResult
from modules.games.infrastructure.clients.itad_client import ItadClient

_BASE = "https://api.isthereanydeal.com"
_GAME_ID = "018d937f-72be-739b-b4a6-c4f07f9c7bd7"
_STEAM_APP_ID = "1245620"

_DEAL_ENTRY = {
    "shop": {"id": "steam", "name": "Steam"},
    "price": {"amount": 29.99, "amountInt": 2999, "currency": "USD"},
    "regular": {"amount": 59.99, "amountInt": 5999, "currency": "USD"},
    "cut": 50,
    "url": "https://store.steampowered.com/app/1245620",
}

_GAME_INFO_RESPONSE = {
    "id": _GAME_ID,
    "title": "Elden Ring",
    "appid": 1245620,
    "assets": {"banner300": "https://cdn.itad.com/elden-ring-300.jpg"},
}


@pytest.fixture
def client() -> ItadClient:
    return ItadClient(api_key="test-api-key")


# ---------------------------------------------------------------------------
# lookup_game_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_game_id_returns_id(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/lookup/v1").mock(
            return_value=httpx.Response(200, json={"found": True, "game": {"id": _GAME_ID}})
        )
        result = await client.lookup_game_id("Elden Ring")

    assert result == _GAME_ID


@pytest.mark.asyncio
async def test_lookup_game_id_returns_none_on_empty_response(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/lookup/v1").mock(return_value=httpx.Response(200, json={"found": False}))
        result = await client.lookup_game_id("Unknown Game")

    assert result is None


@pytest.mark.asyncio
async def test_lookup_game_id_returns_none_on_error(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/lookup/v1").mock(return_value=httpx.Response(500))
        result = await client.lookup_game_id("Some Game")

    assert result is None


# ---------------------------------------------------------------------------
# lookup_game_ids_batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_game_ids_batch_maps_titles(client: ItadClient) -> None:
    titles = ["Elden Ring", "Dark Souls"]
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/lookup/v1", params={"title": "Elden Ring"}).mock(
            return_value=httpx.Response(200, json={"found": True, "game": {"id": "id-1"}})
        )
        mock.get("/games/lookup/v1", params={"title": "Dark Souls"}).mock(
            return_value=httpx.Response(200, json={"found": True, "game": {"id": "id-2"}})
        )
        result = await client.lookup_game_ids_batch(titles)

    assert result["Elden Ring"] == "id-1"
    assert result["Dark Souls"] == "id-2"


@pytest.mark.asyncio
async def test_lookup_game_ids_batch_returns_empty_on_empty_input(
    client: ItadClient,
) -> None:
    result = await client.lookup_game_ids_batch([])
    assert result == {}


# ---------------------------------------------------------------------------
# lookup_game_id_by_steam_app_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_by_steam_app_id_returns_none(client: ItadClient) -> None:
    # The /games/lookup/id/shop/v1 endpoint no longer exists in the ITAD API.
    result = await client.lookup_game_id_by_steam_app_id(_STEAM_APP_ID)
    assert result is None


# ---------------------------------------------------------------------------
# get_prices_for_game
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_prices_returns_list_of_deals(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.post("/games/prices/v2").mock(
            return_value=httpx.Response(200, json=[{"deals": [_DEAL_ENTRY]}])
        )
        result = await client.get_prices_for_game(_GAME_ID, "US")

    assert len(result) == 1
    deal = result[0]
    assert isinstance(deal, Deal)
    assert deal.store_name == "Steam"
    assert deal.price == 29.99
    assert deal.discount == 50
    assert deal.currency == "USD"


@pytest.mark.asyncio
async def test_get_prices_returns_empty_list_on_error(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.post("/games/prices/v2").mock(return_value=httpx.Response(500))
        result = await client.get_prices_for_game(_GAME_ID, "US")

    assert result == []


# ---------------------------------------------------------------------------
# get_prices_for_games_batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_prices_batch_maps_game_ids(client: ItadClient) -> None:
    game_ids = [_GAME_ID, "other-id"]
    with respx.mock(base_url=_BASE) as mock:
        mock.post("/games/prices/v2").mock(
            return_value=httpx.Response(
                200,
                json=[{"deals": [_DEAL_ENTRY]}, {"deals": []}],
            )
        )
        result = await client.get_prices_for_games_batch(game_ids, "US")

    assert len(result[_GAME_ID]) == 1
    assert result["other-id"] == []


# ---------------------------------------------------------------------------
# get_historical_low
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_historical_low_returns_deal(client: ItadClient) -> None:
    low_payload = [
        {
            "shop": {"name": "Steam"},
            "price": {"amount": 9.99, "currency": "USD"},
            "regular": {"amount": 59.99, "currency": "USD"},
            "cut": 83,
            "url": "https://store.steampowered.com/app/1245620",
        }
    ]
    with respx.mock(base_url=_BASE) as mock:
        mock.post("/games/historylow/v1").mock(return_value=httpx.Response(200, json=low_payload))
        result = await client.get_historical_low(_GAME_ID, "US")

    assert isinstance(result, Deal)
    assert result.store_name == "Steam"
    assert result.price == 9.99
    assert result.discount == 83
    assert result.id == f"histlow_{_GAME_ID}"


@pytest.mark.asyncio
async def test_get_historical_low_returns_none_on_empty(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.post("/games/historylow/v1").mock(return_value=httpx.Response(200, json=[]))
        result = await client.get_historical_low(_GAME_ID, "US")

    assert result is None


# ---------------------------------------------------------------------------
# get_game_info
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_game_info_returns_parsed_entity(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/info/v2").mock(return_value=httpx.Response(200, json=_GAME_INFO_RESPONSE))
        result = await client.get_game_info(_GAME_ID)

    assert isinstance(result, ItadGameInfo)
    assert result.title == "Elden Ring"
    assert result.steam_app_id == 1245620
    assert "300" in result.cover_url


@pytest.mark.asyncio
async def test_get_game_info_returns_none_on_error(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/info/v2").mock(return_value=httpx.Response(404))
        result = await client.get_game_info(_GAME_ID)

    assert result is None


# ---------------------------------------------------------------------------
# search_games
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_games_returns_enriched_results(client: ItadClient) -> None:
    search_payload = [
        {
            "id": _GAME_ID,
            "title": "Elden Ring",
            "type": "game",
            "assets": {"banner300": "https://cdn.itad.com/er-300.jpg"},
        }
    ]
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/search/v1").mock(return_value=httpx.Response(200, json=search_payload))
        mock.get("/games/info/v2").mock(return_value=httpx.Response(200, json=_GAME_INFO_RESPONSE))
        results = await client.search_games("Elden Ring")

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, ItadSearchResult)
    assert result.title == "Elden Ring"
    assert result.steam_app_id == 1245620


@pytest.mark.asyncio
async def test_search_games_returns_empty_list_on_error(client: ItadClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get("/games/search/v1").mock(return_value=httpx.Response(500))
        results = await client.search_games("anything")

    assert results == []


# ---------------------------------------------------------------------------
# _sanitize_query
# ---------------------------------------------------------------------------


def test_sanitize_query_removes_trademark_and_registered_symbols() -> None:
    result = ItadClient._sanitize_query("Fallout®️: New Vegas™️")
    assert "®" not in result
    assert "™" not in result
    assert "Fallout" in result
    assert "New Vegas" in result


def test_sanitize_query_removes_superscript_characters() -> None:
    result = ItadClient._sanitize_query("The Elder Scrolls V\u2074")
    assert "\u2074" not in result
    assert "V" not in result or "\u2074" not in result


def test_sanitize_query_normalizes_whitespace() -> None:
    result = ItadClient._sanitize_query("Fallout®️ :   New Vegas™️")
    assert result == "Fallout : New Vegas"


def test_sanitize_query_leaves_plain_titles_unchanged() -> None:
    result = ItadClient._sanitize_query("Hades")
    assert result == "Hades"


def test_sanitize_query_handles_empty_string() -> None:
    result = ItadClient._sanitize_query("")
    assert result == ""


@pytest.mark.asyncio
async def test_search_games_sends_sanitized_title(client: ItadClient) -> None:
    search_payload = [
        {
            "id": _GAME_ID,
            "title": "Fallout: New Vegas",
            "type": "game",
            "assets": {"banner300": "https://cdn.itad.com/fnv-300.jpg"},
        }
    ]
    with respx.mock(base_url=_BASE) as mock:
        search_route = mock.get("/games/search/v1")
        search_route.mock(return_value=httpx.Response(200, json=search_payload))
        info_route = mock.get("/games/info/v2")
        info_route.mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": _GAME_ID,
                    "title": "Fallout: New Vegas",
                    "appid": 22380,
                    "assets": {"banner300": ""},
                },
            )
        )
        results = await client.search_games("Fallout®️: New Vegas™️")

    assert len(results) == 1
    assert search_route.called
    title_param = search_route.calls[0].request.url.params.get("title", "")
    assert "®" not in title_param
    assert "™" not in title_param
