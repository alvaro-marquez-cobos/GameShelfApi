"""HTTP router tests for the search module."""

from unittest.mock import AsyncMock

from httpx import AsyncClient

from modules.search.domain.entities.search_result import SearchResult
from shared.domain.enums.platform import Platform


def _result(
    game_id: str = "itad-uuid-1",
    title: str = "Dota 2",
    is_owned: bool = False,
    owned_platforms: list[Platform] | None = None,
    is_in_wishlist: bool = False,
    steam_app_id: int | None = 570,
) -> SearchResult:
    return SearchResult(
        id=game_id,
        title=title,
        cover_url="https://cdn.example.com/cover.jpg",
        steam_app_id=steam_app_id,
        is_owned=is_owned,
        owned_platforms=owned_platforms or [],
        is_in_wishlist=is_in_wishlist,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/search?q=
# ---------------------------------------------------------------------------


async def test_search_returns_results(
    async_client: AsyncClient,
    mock_search_use_case: AsyncMock,
) -> None:
    mock_search_use_case.execute = AsyncMock(return_value=[_result()])

    response = await async_client.get(
        "/api/v1/search",
        headers={"Authorization": "Bearer valid-token"},
        params={"q": "dota"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "itad-uuid-1"
    assert data["results"][0]["title"] == "Dota 2"
    assert data["results"][0]["steamAppId"] == 570
    assert data["results"][0]["isOwned"] is False
    assert data["results"][0]["ownedPlatforms"] == []
    assert data["results"][0]["isInWishlist"] is False


async def test_search_owned_game_shows_correct_platform(
    async_client: AsyncClient,
    mock_search_use_case: AsyncMock,
) -> None:
    mock_search_use_case.execute = AsyncMock(
        return_value=[_result(is_owned=True, owned_platforms=[Platform.STEAM])]
    )

    response = await async_client.get(
        "/api/v1/search",
        headers={"Authorization": "Bearer valid-token"},
        params={"q": "dota"},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["isOwned"] is True
    assert result["ownedPlatforms"] == ["steam"]


async def test_search_wishlist_game_flagged(
    async_client: AsyncClient,
    mock_search_use_case: AsyncMock,
) -> None:
    mock_search_use_case.execute = AsyncMock(return_value=[_result(is_in_wishlist=True)])

    response = await async_client.get(
        "/api/v1/search",
        headers={"Authorization": "Bearer valid-token"},
        params={"q": "dota"},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["isInWishlist"] is True


async def test_search_empty_results(
    async_client: AsyncClient,
    mock_search_use_case: AsyncMock,
) -> None:
    mock_search_use_case.execute = AsyncMock(return_value=[])

    response = await async_client.get(
        "/api/v1/search",
        headers={"Authorization": "Bearer valid-token"},
        params={"q": "xyznonexistent"},
    )

    assert response.status_code == 200
    assert response.json()["results"] == []


async def test_search_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/search", params={"q": "dota"})
    assert response.status_code == 401


async def test_search_missing_query_param(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/search",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 422


async def test_search_empty_query_param_rejected(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/search",
        headers={"Authorization": "Bearer valid-token"},
        params={"q": ""},
    )
    assert response.status_code == 422


async def test_search_passes_uid_and_query_to_use_case(
    async_client: AsyncClient,
    mock_search_use_case: AsyncMock,
) -> None:
    mock_search_use_case.execute = AsyncMock(return_value=[])

    await async_client.get(
        "/api/v1/search",
        headers={"Authorization": "Bearer valid-token"},
        params={"q": "half-life"},
    )

    mock_search_use_case.execute.assert_awaited_once_with("test-uid-123", "half-life")
