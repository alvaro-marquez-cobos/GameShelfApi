"""Tests for GetLibraryUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.library.application.get_library_use_case import GetLibraryUseCase
from modules.library.domain.entities.library_game import LibraryGame
from modules.library.domain.enums.library import LibrarySortBy, LibraryTab
from shared.domain.enums.platform import Platform


def _game(
    game_id: str,
    title: str,
    platform: Platform = Platform.STEAM,
    playtime: int = 0,
    last_played: str | None = None,
) -> LibraryGame:
    return LibraryGame(
        game_id=game_id,
        title=title,
        platform=platform,
        playtime_minutes=playtime,
        last_played=last_played,
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock) -> GetLibraryUseCase:
    return GetLibraryUseCase(repo)


# ---------------------------------------------------------------------------
# Tab filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tab_all_returns_all_games(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Game A", Platform.STEAM),
        _game("psn_1", "Game B", Platform.PSN),
        _game("epic_1", "Game C", Platform.EPIC),
    ]
    games, total = await use_case.execute("uid", tab=LibraryTab.ALL)

    assert total == 3
    assert len(games) == 3


@pytest.mark.asyncio
async def test_tab_pc_filters_steam_epic_gog(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Steam Game", Platform.STEAM),
        _game("epic_1", "Epic Game", Platform.EPIC),
        _game("gog_1", "GOG Game", Platform.GOG),
        _game("psn_1", "PSN Game", Platform.PSN),
    ]
    games, total = await use_case.execute("uid", tab=LibraryTab.PC)

    assert total == 3
    assert all(g.platform != Platform.PSN for g in games)


@pytest.mark.asyncio
async def test_tab_console_filters_psn_only(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Steam Game", Platform.STEAM),
        _game("psn_1", "PSN Game 1", Platform.PSN),
        _game("psn_2", "PSN Game 2", Platform.PSN),
    ]
    games, total = await use_case.execute("uid", tab=LibraryTab.CONSOLE)

    assert total == 2
    assert all(g.platform == Platform.PSN for g in games)


# ---------------------------------------------------------------------------
# Search filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_is_case_insensitive(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("s1", "The Legend of Zelda"),
        _game("s2", "Hades"),
        _game("s3", "ZELDA: Breath of the Wild"),
    ]
    games, total = await use_case.execute("uid", search="zelda")

    assert total == 2
    assert all("zelda" in g.title.lower() for g in games)


@pytest.mark.asyncio
async def test_search_empty_string_returns_all(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [_game("s1", "A"), _game("s2", "B")]
    _, total = await use_case.execute("uid", search="")

    assert total == 2


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sort_alphabetical(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("s3", "Zelda"),
        _game("s1", "Celeste"),
        _game("s2", "Hades"),
    ]
    games, _ = await use_case.execute("uid", sort_by=LibrarySortBy.ALPHABETICAL)

    assert [g.title for g in games] == ["Celeste", "Hades", "Zelda"]


@pytest.mark.asyncio
async def test_sort_playtime_descending(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("s1", "A", playtime=100),
        _game("s2", "B", playtime=500),
        _game("s3", "C", playtime=250),
    ]
    games, _ = await use_case.execute("uid", sort_by=LibrarySortBy.PLAYTIME)

    assert games[0].playtime_minutes == 500
    assert games[1].playtime_minutes == 250
    assert games[2].playtime_minutes == 100


@pytest.mark.asyncio
async def test_sort_last_played_descending(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("s1", "A", last_played="2026-01-01"),
        _game("s2", "B", last_played="2026-03-01"),
        _game("s3", "C", last_played="2026-02-01"),
    ]
    games, _ = await use_case.execute("uid", sort_by=LibrarySortBy.LAST_PLAYED)

    assert games[0].last_played == "2026-03-01"
    assert games[1].last_played == "2026-02-01"


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_offset_and_limit(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    # Zero-padded titles so alphabetical sort is predictable
    repo.get_games.return_value = [_game(f"s{i:02d}", f"Game {i:02d}") for i in range(25)]
    games, total = await use_case.execute("uid", offset=10, limit=5)

    assert total == 25
    assert len(games) == 5
    assert games[0].game_id == "s10"


@pytest.mark.asyncio
async def test_pagination_returns_empty_beyond_total(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [_game("s1", "Only Game")]
    games, total = await use_case.execute("uid", offset=10, limit=5)

    assert total == 1
    assert games == []
