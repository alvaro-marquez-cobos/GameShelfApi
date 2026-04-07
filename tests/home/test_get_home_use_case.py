"""Tests for GetHomeUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.home.application.get_home_use_case import GetHomeUseCase
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


def _steam_game(app_id: int, name: str, playtime: int = 100) -> MagicMock:
    g = MagicMock()
    g.app_id = app_id
    g.name = name
    g.playtime_forever = playtime
    g.header_image = f"https://img/{app_id}.jpg"
    g.last_played = 0
    return g


def _library_game(game_id: str, playtime: int = 100) -> LibraryGame:
    return LibraryGame(
        game_id=game_id,
        title=game_id,
        platform=Platform.STEAM,
        playtime_minutes=playtime,
    )


@pytest.fixture
def steam_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def library_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def platform_reader() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    steam_client: AsyncMock,
    library_repo: AsyncMock,
    platform_reader: AsyncMock,
) -> GetHomeUseCase:
    return GetHomeUseCase(steam_client, library_repo, platform_reader)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_home_data_with_steam_linked(
    use_case: GetHomeUseCase,
    steam_client: AsyncMock,
    library_repo: AsyncMock,
    platform_reader: AsyncMock,
) -> None:
    platform_reader.get_linked_platforms.return_value = [
        LinkedPlatform(platform=Platform.STEAM, username="76561198000000001")
    ]
    steam_client.get_recently_played.return_value = [_steam_game(570, "Dota 2", playtime=200)]
    library_repo.get_most_played.return_value = [
        _library_game("steam_570", playtime=500),
        _library_game("steam_440", playtime=300),
        _library_game("steam_730", playtime=100),
    ]
    steam_client.get_most_played_global.return_value = [_steam_game(570, "Dota 2", playtime=800000)]

    result = await use_case.execute("uid_abc")

    assert result.recently_played is not None
    assert len(result.recently_played) == 1
    assert result.recently_played[0].game_id == "steam_570"

    assert len(result.most_played) == 3
    assert result.most_played[0].game_id == "steam_570"  # highest playtime

    assert result.popular_now is not None
    assert result.popular_now[0].steam_app_id == 570


@pytest.mark.asyncio
async def test_most_played_capped_at_five(
    use_case: GetHomeUseCase,
    steam_client: AsyncMock,
    library_repo: AsyncMock,
    platform_reader: AsyncMock,
) -> None:
    platform_reader.get_linked_platforms.return_value = []
    # Repo already applies order + limit=5, so the mock returns the top 5 pre-sorted.
    library_repo.get_most_played.return_value = [
        _library_game(f"steam_{i}", playtime=i * 10) for i in range(9, 4, -1)
    ]
    steam_client.get_most_played_global.return_value = []

    result = await use_case.execute("uid_abc")

    assert len(result.most_played) == 5
    # Top 5 by playtime desc: steam_9 first
    assert result.most_played[0].game_id == "steam_9"


# ---------------------------------------------------------------------------
# No Steam linked
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recently_played_is_none_when_steam_not_linked(
    use_case: GetHomeUseCase,
    steam_client: AsyncMock,
    library_repo: AsyncMock,
    platform_reader: AsyncMock,
) -> None:
    platform_reader.get_linked_platforms.return_value = []
    library_repo.get_most_played.return_value = []
    steam_client.get_most_played_global.return_value = []

    result = await use_case.execute("uid_abc")

    assert result.recently_played is None
    steam_client.get_recently_played.assert_not_awaited()


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recently_played_failure_returns_none(
    use_case: GetHomeUseCase,
    steam_client: AsyncMock,
    library_repo: AsyncMock,
    platform_reader: AsyncMock,
) -> None:
    platform_reader.get_linked_platforms.return_value = [
        LinkedPlatform(platform=Platform.STEAM, username="76561198000000001")
    ]
    steam_client.get_recently_played.side_effect = Exception("Steam API down")
    library_repo.get_most_played.return_value = []
    steam_client.get_most_played_global.return_value = []

    result = await use_case.execute("uid_abc")

    assert result.recently_played is None
    assert result.most_played == []


@pytest.mark.asyncio
async def test_popular_now_failure_returns_none(
    use_case: GetHomeUseCase,
    steam_client: AsyncMock,
    library_repo: AsyncMock,
    platform_reader: AsyncMock,
) -> None:
    platform_reader.get_linked_platforms.return_value = []
    library_repo.get_most_played.return_value = [_library_game("steam_570")]
    steam_client.get_most_played_global.side_effect = Exception("Steam Charts down")

    result = await use_case.execute("uid_abc")

    assert result.popular_now is None
    assert len(result.most_played) == 1
