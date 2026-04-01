"""HTTP router tests for the home module."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from httpx import AsyncClient

from shared.domain.enums.platform import Platform


def _library_game(
    game_id: str = "steam_570",
    title: str = "Dota 2",
    playtime: int = 3600,
    steam_app_id: int | None = 570,
) -> SimpleNamespace:
    return SimpleNamespace(
        game_id=game_id,
        title=title,
        platform=Platform.STEAM,
        cover_url="https://cdn.steam.com/cover.jpg",
        playtime_minutes=playtime,
        last_played=None,
        steam_app_id=steam_app_id,
    )


def _popular_game(
    steam_app_id: int = 570,
    title: str = "Dota 2",
    current_players: int = 500_000,
) -> SimpleNamespace:
    return SimpleNamespace(
        steam_app_id=steam_app_id,
        title=title,
        current_players=current_players,
        cover_url="https://cdn.steam.com/cover.jpg",
    )


def _home_data(
    recently_played: list[SimpleNamespace] | None = None,
    most_played: list[SimpleNamespace] | None = None,
    popular_now: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        recently_played=recently_played,
        most_played=most_played or [],
        popular_now=popular_now,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/home
# ---------------------------------------------------------------------------


async def test_get_home_with_all_sections(
    async_client: AsyncClient,
    mock_get_home_use_case: AsyncMock,
) -> None:
    mock_get_home_use_case.execute = AsyncMock(
        return_value=_home_data(
            recently_played=[_library_game()],
            most_played=[_library_game(title="CS2", game_id="steam_730", steam_app_id=730)],
            popular_now=[_popular_game()],
        )
    )

    response = await async_client.get(
        "/api/v1/home",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["recentlyPlayed"]) == 1
    assert data["recentlyPlayed"][0]["gameId"] == "steam_570"
    assert len(data["mostPlayed"]) == 1
    assert len(data["popularNow"]) == 1
    assert data["popularNow"][0]["currentPlayers"] == 500_000


async def test_get_home_optional_sections_null_when_missing(
    async_client: AsyncClient,
    mock_get_home_use_case: AsyncMock,
) -> None:
    mock_get_home_use_case.execute = AsyncMock(
        return_value=_home_data(most_played=[_library_game()])
    )

    response = await async_client.get(
        "/api/v1/home",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["recentlyPlayed"] is None
    assert data["popularNow"] is None
    assert len(data["mostPlayed"]) == 1


async def test_get_home_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/home")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/home/popular
# ---------------------------------------------------------------------------


async def test_get_popular_returns_games(
    async_client: AsyncClient,
    mock_get_home_use_case: AsyncMock,
) -> None:
    games = [
        _popular_game(steam_app_id=i, title=f"Game {i}", current_players=i * 1000)
        for i in range(1, 6)
    ]
    mock_get_home_use_case.execute = AsyncMock(return_value=_home_data(popular_now=games))

    response = await async_client.get(
        "/api/v1/home/popular",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["games"]) == 5
    assert data["games"][0]["steamAppId"] == 1


async def test_get_popular_respects_limit(
    async_client: AsyncClient,
    mock_get_home_use_case: AsyncMock,
) -> None:
    games = [_popular_game(steam_app_id=i, title=f"Game {i}") for i in range(1, 11)]
    mock_get_home_use_case.execute = AsyncMock(return_value=_home_data(popular_now=games))

    response = await async_client.get(
        "/api/v1/home/popular",
        headers={"Authorization": "Bearer valid-token"},
        params={"limit": 3},
    )

    assert response.status_code == 200
    assert len(response.json()["games"]) == 3


async def test_get_popular_empty_when_no_data(
    async_client: AsyncClient,
    mock_get_home_use_case: AsyncMock,
) -> None:
    mock_get_home_use_case.execute = AsyncMock(return_value=_home_data(popular_now=None))

    response = await async_client.get(
        "/api/v1/home/popular",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["games"] == []


async def test_get_popular_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/home/popular")
    assert response.status_code == 401


async def test_get_popular_limit_out_of_range(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/home/popular",
        headers={"Authorization": "Bearer valid-token"},
        params={"limit": 0},
    )
    assert response.status_code == 422
