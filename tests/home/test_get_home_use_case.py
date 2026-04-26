"""Tests for GetHomeUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.home.application.get_home_use_case import GetHomeUseCase
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.popular_game import PopularGame
from shared.domain.enums.platform import Platform


def _library_game(game_id: str, playtime: int = 100) -> LibraryGame:
    return LibraryGame(
        game_id=game_id,
        title=game_id,
        platform=Platform.STEAM,
        playtime_minutes=playtime,
    )


def _popular(app_id: int, title: str, players: int = 1000) -> PopularGame:
    return PopularGame(
        game_id=f"steam_{app_id}",
        steam_app_id=app_id,
        title=title,
        current_players=players,
        cover_url=f"https://img/{app_id}.jpg",
    )


@pytest.fixture
def content_provider() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def library_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    content_provider: AsyncMock,
    library_repo: AsyncMock,
) -> GetHomeUseCase:
    return GetHomeUseCase(content_provider, library_repo)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_home_data(
    use_case: GetHomeUseCase,
    content_provider: AsyncMock,
    library_repo: AsyncMock,
) -> None:
    content_provider.get_recently_played.return_value = [_library_game("steam_570", playtime=200)]
    library_repo.get_most_played.return_value = [
        _library_game("steam_570", playtime=500),
        _library_game("steam_440", playtime=300),
        _library_game("steam_730", playtime=100),
    ]
    content_provider.get_globally_popular.return_value = [_popular(570, "Dota 2", players=800000)]

    result = await use_case.execute("uid_abc")

    assert result.recently_played is not None
    assert len(result.recently_played) == 1
    assert result.recently_played[0].game_id == "steam_570"

    assert len(result.most_played) == 3
    assert result.most_played[0].game_id == "steam_570"

    assert result.popular_now is not None
    assert result.popular_now[0].steam_app_id == 570


@pytest.mark.asyncio
async def test_most_played_capped_at_five(
    use_case: GetHomeUseCase,
    content_provider: AsyncMock,
    library_repo: AsyncMock,
) -> None:
    content_provider.get_recently_played.return_value = None
    library_repo.get_most_played.return_value = [
        _library_game(f"steam_{i}", playtime=i * 10) for i in range(9, 4, -1)
    ]
    content_provider.get_globally_popular.return_value = []

    result = await use_case.execute("uid_abc")

    assert len(result.most_played) == 5
    assert result.most_played[0].game_id == "steam_9"


# ---------------------------------------------------------------------------
# Provider returns None for recently played
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recently_played_is_none_when_provider_returns_none(
    use_case: GetHomeUseCase,
    content_provider: AsyncMock,
    library_repo: AsyncMock,
) -> None:
    content_provider.get_recently_played.return_value = None
    library_repo.get_most_played.return_value = []
    content_provider.get_globally_popular.return_value = []

    result = await use_case.execute("uid_abc")

    assert result.recently_played is None


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recently_played_failure_returns_none(
    use_case: GetHomeUseCase,
    content_provider: AsyncMock,
    library_repo: AsyncMock,
) -> None:
    content_provider.get_recently_played.side_effect = Exception("Provider down")
    library_repo.get_most_played.return_value = []
    content_provider.get_globally_popular.return_value = []

    result = await use_case.execute("uid_abc")

    assert result.recently_played is None
    assert result.most_played == []


@pytest.mark.asyncio
async def test_popular_now_failure_returns_empty_list(
    use_case: GetHomeUseCase,
    content_provider: AsyncMock,
    library_repo: AsyncMock,
) -> None:
    content_provider.get_recently_played.return_value = None
    library_repo.get_most_played.return_value = [_library_game("steam_570")]
    content_provider.get_globally_popular.side_effect = Exception("Provider down")

    result = await use_case.execute("uid_abc")

    assert result.popular_now == []
    assert len(result.most_played) == 1
