"""Tests for SteamMetadataClient."""

import httpx
import pytest
import respx

from modules.games.domain.entities.steam import SteamAppDetails
from modules.games.infrastructure.clients.steam_metadata_client import (
    SteamMetadataClient,
    _normalize,
)


@pytest.fixture
def client() -> SteamMetadataClient:
    return SteamMetadataClient()


_APP_ID = 570
_APP_DETAILS_PAYLOAD = {
    str(_APP_ID): {
        "success": True,
        "data": {
            "type": "game",
            "name": "Dota 2",
            "short_description": "Dota 2 is a multiplayer online battle arena.",
            "header_image": "https://cdn.steam.com/dota2.jpg",
            "genres": [{"id": "1", "description": "Action"}],
            "developers": ["Valve"],
            "publishers": ["Valve"],
            "release_date": {"coming_soon": False, "date": "9 Jul, 2013"},
            "metacritic": {"score": 90, "url": "https://metacritic.com/dota2"},
            "screenshots": [{"id": 0, "path_full": "https://cdn.steam.com/ss1.jpg"}],
            "recommendations": {"total": 1000000},
        },
    }
}


# ---------------------------------------------------------------------------
# get_app_details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_app_details_returns_parsed_entity(client: SteamMetadataClient) -> None:
    with respx.mock(base_url="https://store.steampowered.com") as mock:
        mock.get("/api/appdetails").mock(
            return_value=httpx.Response(200, json=_APP_DETAILS_PAYLOAD)
        )
        result = await client.get_app_details(_APP_ID)

    assert isinstance(result, SteamAppDetails)
    assert result.name == "Dota 2"
    assert result.genres == ["Action"]
    assert result.metacritic_score == 90
    assert result.release_date == "9 Jul, 2013"
    assert result.screenshots == ["https://cdn.steam.com/ss1.jpg"]


@pytest.mark.asyncio
async def test_get_app_details_returns_none_when_success_false(client: SteamMetadataClient) -> None:
    payload = {str(_APP_ID): {"success": False}}
    with respx.mock(base_url="https://store.steampowered.com") as mock:
        mock.get("/api/appdetails").mock(return_value=httpx.Response(200, json=payload))
        result = await client.get_app_details(_APP_ID)

    assert result is None


@pytest.mark.asyncio
async def test_get_app_details_returns_none_on_http_error(client: SteamMetadataClient) -> None:
    with respx.mock(base_url="https://store.steampowered.com") as mock:
        mock.get("/api/appdetails").mock(return_value=httpx.Response(500))
        result = await client.get_app_details(_APP_ID)

    assert result is None


# ---------------------------------------------------------------------------
# search_store
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_store_returns_app_id_on_exact_match(client: SteamMetadataClient) -> None:
    payload = {"items": [{"id": 570, "name": "Dota 2"}]}
    with respx.mock(base_url="https://store.steampowered.com") as mock:
        mock.get("/api/storesearch/").mock(return_value=httpx.Response(200, json=payload))
        result = await client.search_store("Dota 2")

    assert result == 570


@pytest.mark.asyncio
async def test_search_store_returns_app_id_on_word_overlap(client: SteamMetadataClient) -> None:
    payload = {"items": [{"id": 570, "name": "Dota 2: Reborn"}]}
    with respx.mock(base_url="https://store.steampowered.com") as mock:
        mock.get("/api/storesearch/").mock(return_value=httpx.Response(200, json=payload))
        result = await client.search_store("Dota 2")

    assert result == 570


@pytest.mark.asyncio
async def test_search_store_returns_none_when_no_results(client: SteamMetadataClient) -> None:
    payload: dict[str, list[dict[str, object]]] = {"items": []}
    with respx.mock(base_url="https://store.steampowered.com") as mock:
        mock.get("/api/storesearch/").mock(return_value=httpx.Response(200, json=payload))
        result = await client.search_store("Nonexistent Game XYZ")

    assert result is None


@pytest.mark.asyncio
async def test_search_store_returns_none_on_http_error(client: SteamMetadataClient) -> None:
    with respx.mock(base_url="https://store.steampowered.com") as mock:
        mock.get("/api/storesearch/").mock(return_value=httpx.Response(503))
        result = await client.search_store("Dota 2")

    assert result is None


# ---------------------------------------------------------------------------
# _normalize — special characters and diacritics
# ---------------------------------------------------------------------------


def test_normalize_strips_registered_trademark_symbol() -> None:
    assert _normalize("The Last of Us Part II®") == "the last of us part ii"


def test_normalize_stips_trademark_symbol() -> None:
    assert _normalize("Metro 2033™") == "metro 2033"


def test_normalize_converts_copyright_symbol() -> None:
    assert _normalize("Castlevania ©1986") == "castlevania 1986"


def test_normalize_preserves_roman_numerals() -> None:
    assert _normalize("Final Fantasy Ⅱ") == "final fantasy ii"


def test_normalize_strips_accents_via_decomposition() -> None:
    assert _normalize("Léon: The Professional") == "leon the professional"


def test_normalize_strips_degree_symbol() -> None:
    assert _normalize("Call of Duty® Modern Warfare™ 2") == "call of duty modern warfare 2"


def test_normalize_preserves_spaces_and_numbers() -> None:
    assert _normalize("Grand Theft Auto V") == "grand theft auto v"


def test_normalize_handles_colons_and_parens() -> None:
    expected = "the witcher 3 wild hunt goty edition"
    assert _normalize("The Witcher 3: Wild Hunt (GOTY Edition)") == expected


def test_normalize_matches_with_special_chars_on_both_sides() -> None:
    needle = _normalize("The Last of Us Part II®")
    candidate = _normalize("The Last of Us Part II™")
    assert needle == candidate
