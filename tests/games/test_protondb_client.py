"""Tests for ProtonDbClient."""

import httpx
import pytest
import respx

from modules.games.domain.entities.protondb import ProtonDbRating
from modules.games.infrastructure.clients.protondb_client import ProtonDbClient

_APP_ID = "570"
_BASE = "https://www.protondb.com"
_PATH = f"/api/v1/reports/summaries/{_APP_ID}.json"

_RATING_PAYLOAD = {
    "tier": "gold",
    "trendingTier": "platinum",
    "bestReportedTier": "platinum",
    "total": 1200,
    "score": 0.9,
    "confidence": "good",
}


@pytest.fixture
def client() -> ProtonDbClient:
    return ProtonDbClient()


# ---------------------------------------------------------------------------
# get_compatibility_rating — success cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_parsed_rating(client: ProtonDbClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get(_PATH).mock(return_value=httpx.Response(200, json=_RATING_PAYLOAD))
        result = await client.get_compatibility_rating(_APP_ID)

    assert isinstance(result, ProtonDbRating)
    assert result.tier == "gold"
    assert result.trending_tier == "platinum"
    assert result.total == 1200


@pytest.mark.asyncio
async def test_falls_back_to_tier_when_trending_missing(client: ProtonDbClient) -> None:
    payload = {**_RATING_PAYLOAD, "trendingTier": None}
    with respx.mock(base_url=_BASE) as mock:
        mock.get(_PATH).mock(return_value=httpx.Response(200, json=payload))
        result = await client.get_compatibility_rating(_APP_ID)

    assert result is not None
    assert result.trending_tier == "gold"


@pytest.mark.asyncio
async def test_unknown_tier_falls_back_to_pending(client: ProtonDbClient) -> None:
    payload = {**_RATING_PAYLOAD, "tier": "unknown_value"}
    with respx.mock(base_url=_BASE) as mock:
        mock.get(_PATH).mock(return_value=httpx.Response(200, json=payload))
        result = await client.get_compatibility_rating(_APP_ID)

    assert result is not None
    assert result.tier == "pending"


# ---------------------------------------------------------------------------
# get_compatibility_rating — failure / edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_none_on_404(client: ProtonDbClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get(_PATH).mock(return_value=httpx.Response(404))
        result = await client.get_compatibility_rating(_APP_ID)

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_on_server_error(client: ProtonDbClient) -> None:
    with respx.mock(base_url=_BASE) as mock:
        mock.get(_PATH).mock(return_value=httpx.Response(500))
        result = await client.get_compatibility_rating(_APP_ID)

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_for_non_numeric_app_id(client: ProtonDbClient) -> None:
    result = await client.get_compatibility_rating("not-a-number")
    assert result is None


@pytest.mark.asyncio
async def test_all_valid_tiers_are_accepted(client: ProtonDbClient) -> None:
    valid_tiers = ["platinum", "gold", "silver", "bronze", "borked", "pending"]
    for tier in valid_tiers:
        payload = {**_RATING_PAYLOAD, "tier": tier, "trendingTier": tier}
        with respx.mock(base_url=_BASE) as mock:
            mock.get(_PATH).mock(return_value=httpx.Response(200, json=payload))
            result = await client.get_compatibility_rating(_APP_ID)

        assert result is not None
        assert result.tier == tier
