"""Tests for GetLibraryStatsUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.library.application.get_library_stats_use_case import GetLibraryStatsUseCase
from modules.library.domain.entities.library_game import LibraryGame
from shared.domain.enums.platform import Platform


def _game(game_id: str, platform: Platform, playtime: int = 0) -> LibraryGame:
    return LibraryGame(game_id=game_id, title="Game", platform=platform, playtime_minutes=playtime)


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock) -> GetLibraryStatsUseCase:
    return GetLibraryStatsUseCase(repo)


@pytest.mark.asyncio
async def test_stats_all_platforms(use_case: GetLibraryStatsUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", Platform.STEAM, playtime=120),
        _game("epic_1", Platform.EPIC, playtime=60),
        _game("gog_1", Platform.GOG, playtime=30),
        _game("psn_1", Platform.PSN, playtime=90),
        _game("psn_2", Platform.PSN, playtime=150),
    ]

    stats = await use_case.execute("uid_abc")

    assert stats.total == 5
    assert stats.pc_games == 3
    assert stats.console_games == 2
    assert stats.total_playtime_hours == round(450 / 60, 2)


@pytest.mark.asyncio
async def test_stats_empty_library(use_case: GetLibraryStatsUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = []

    stats = await use_case.execute("uid_abc")

    assert stats.total == 0
    assert stats.pc_games == 0
    assert stats.console_games == 0
    assert stats.total_playtime_hours == 0.0


@pytest.mark.asyncio
async def test_stats_playtime_converted_to_hours(
    use_case: GetLibraryStatsUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("s1", Platform.STEAM, playtime=90),  # 1.5h
        _game("s2", Platform.STEAM, playtime=150),  # 2.5h
    ]

    stats = await use_case.execute("uid_abc")

    assert stats.total_playtime_hours == 4.0


@pytest.mark.asyncio
async def test_stats_pc_only_library(use_case: GetLibraryStatsUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("s1", Platform.STEAM),
        _game("e1", Platform.EPIC),
        _game("g1", Platform.GOG),
    ]

    stats = await use_case.execute("uid_abc")

    assert stats.pc_games == 3
    assert stats.console_games == 0
