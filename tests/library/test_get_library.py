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
    game_type: str | None = None,
    parent_game_id: str | None = None,
) -> LibraryGame:
    return LibraryGame(
        game_id=game_id,
        title=title,
        platform=platform,
        playtime_minutes=playtime,
        last_played=last_played,
        game_type=game_type,
        parent_game_id=parent_game_id,
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
    games, total, platforms_list = await use_case.execute("uid", tab=LibraryTab.ALL)

    assert total == 3
    assert len(games) == 3
    assert len(platforms_list) == 3


@pytest.mark.asyncio
async def test_tab_pc_filters_steam_epic_gog(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Steam Game", Platform.STEAM),
        _game("epic_1", "Epic Game", Platform.EPIC),
        _game("gog_1", "GOG Game", Platform.GOG),
        _game("psn_1", "PSN Game", Platform.PSN),
    ]
    games, total, platforms_list = await use_case.execute("uid", tab=LibraryTab.PC)

    assert total == 3
    assert len(games) == 3
    assert all(g.platform != Platform.PSN for g in games)
    assert len(platforms_list) == 3


@pytest.mark.asyncio
async def test_tab_console_filters_psn_only(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Steam Game", Platform.STEAM),
        _game("psn_1", "PSN Game 1", Platform.PSN),
        _game("psn_2", "PSN Game 2", Platform.PSN),
    ]
    games, total, platforms_list = await use_case.execute("uid", tab=LibraryTab.CONSOLE)

    assert total == 2
    assert len(games) == 2
    assert all(g.platform == Platform.PSN for g in games)
    assert len(platforms_list) == 2


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
    games, total, platforms_list = await use_case.execute("uid", search="zelda")

    assert total == 2
    assert len(games) == 2
    assert all("zelda" in g.title.lower() for g in games)
    assert len(platforms_list) == 2


@pytest.mark.asyncio
async def test_search_empty_string_returns_all(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("s1", "Game A"),
        _game("s2", "Game B"),
    ]
    _, total, platforms_list = await use_case.execute("uid", search="")

    assert total == 2
    assert len(platforms_list) == 2


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
    games, _, platforms_list = await use_case.execute("uid", sort_by=LibrarySortBy.ALPHABETICAL)

    assert [g.title for g in games] == ["Celeste", "Hades", "Zelda"]
    assert len(platforms_list) == 3


@pytest.mark.asyncio
async def test_sort_playtime_descending(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("s1", "A", playtime=100),
        _game("s2", "B", playtime=500),
        _game("s3", "C", playtime=250),
    ]
    games, _, platforms_list = await use_case.execute("uid", sort_by=LibrarySortBy.PLAYTIME)

    assert games[0].playtime_minutes == 500
    assert games[1].playtime_minutes == 250
    assert games[2].playtime_minutes == 100
    assert len(platforms_list) == 3


@pytest.mark.asyncio
async def test_sort_last_played_descending(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("s1", "A", last_played="2026-01-01"),
        _game("s2", "B", last_played="2026-03-01"),
        _game("s3", "C", last_played="2026-02-01"),
    ]
    games, _, platforms_list = await use_case.execute("uid", sort_by=LibrarySortBy.LAST_PLAYED)

    assert games[0].last_played == "2026-03-01"
    assert games[1].last_played == "2026-02-01"
    assert len(platforms_list) == 3


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_offset_and_limit(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [_game(f"s{i:02d}", f"Game {i:02d}") for i in range(25)]
    games, total, platforms_list = await use_case.execute("uid", offset=10, limit=5)

    assert total == 25
    assert len(games) == 5
    assert games[0].game_id == "s10"
    assert len(platforms_list) == 5


@pytest.mark.asyncio
async def test_pagination_returns_empty_beyond_total(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [_game("s1", "Only Game")]
    games, total, platforms_list = await use_case.execute("uid", offset=10, limit=5)

    assert total == 1
    assert games == []
    assert len(platforms_list) == 0


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_merge_groups_same_title_different_platforms(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Elden Ring", Platform.STEAM),
        _game("psn_1", "Elden Ring", Platform.PSN),
    ]
    games, total, platforms_list = await use_case.execute("uid")

    assert total == 1
    assert len(games) == 1
    assert games[0].platform == Platform.STEAM
    assert platforms_list[0] == [Platform.STEAM, Platform.PSN]


@pytest.mark.asyncio
async def test_merge_prefers_steam_as_canonical(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("epic_1", "God of War", Platform.EPIC),
        _game("steam_1", "God of War", Platform.STEAM),
        _game("gog_1", "God of War", Platform.GOG),
    ]
    games, total, platforms_list = await use_case.execute("uid")

    assert total == 1
    assert len(games) == 1
    assert games[0].platform == Platform.STEAM
    assert set(platforms_list[0]) == {Platform.EPIC, Platform.STEAM, Platform.GOG}


@pytest.mark.asyncio
async def test_merge_excludes_dlc_by_game_type(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Cyberpunk 2077", Platform.STEAM),
        _game("steam_2", "Phantom Liberty", Platform.STEAM, game_type="DLC"),
    ]
    games, total, _platforms_list = await use_case.execute("uid")

    assert total == 1
    assert len(games) == 1
    assert games[0].title == "Cyberpunk 2077"


@pytest.mark.asyncio
async def test_merge_excludes_dlc_by_parent_game_id(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "The Witcher 3", Platform.STEAM),
        _game("steam_2", "Hearts of Stone", Platform.STEAM, parent_game_id="steam_1"),
    ]
    games, total, _platforms_list = await use_case.execute("uid")

    assert total == 1
    assert len(games) == 1
    assert games[0].title == "The Witcher 3"


@pytest.mark.asyncio
async def test_merge_no_duplicates_when_single_platform(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Game A", Platform.STEAM),
        _game("epic_1", "Game B", Platform.EPIC),
    ]
    games, total, platforms_list = await use_case.execute("uid")

    assert total == 2
    assert len(games) == 2
    assert platforms_list[0] == [Platform.STEAM]
    assert platforms_list[1] == [Platform.EPIC]


# ---------------------------------------------------------------------------
# Platform filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_filter_single_platform(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Game A", Platform.STEAM),
        _game("epic_1", "Game B", Platform.EPIC),
        _game("gog_1", "Game C", Platform.GOG),
    ]
    games, total, _platforms_list = await use_case.execute("uid", platforms=[Platform.STEAM])

    assert total == 1
    assert len(games) == 1
    assert games[0].platform == Platform.STEAM


@pytest.mark.asyncio
async def test_platform_filter_multiple_platforms(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Game A", Platform.STEAM),
        _game("epic_1", "Game B", Platform.EPIC),
        _game("gog_1", "Game C", Platform.GOG),
        _game("psn_1", "Game D", Platform.PSN),
    ]
    games, total, _platforms_list = await use_case.execute(
        "uid", platforms=[Platform.STEAM, Platform.GOG]
    )

    assert total == 2
    assert len(games) == 2
    assert set(g.platform for g in games) == {Platform.STEAM, Platform.GOG}


@pytest.mark.asyncio
async def test_platform_filter_empty_list_returns_all(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "A"),
        _game("epic_1", "B"),
    ]
    games, total, _platforms_list = await use_case.execute("uid", platforms=[])

    assert total == 2
    assert len(games) == 2


@pytest.mark.asyncio
async def test_platform_filter_no_match_returns_empty(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "A", Platform.STEAM),
    ]
    games, total, platforms_list = await use_case.execute("uid", platforms=[Platform.PSN])

    assert total == 0
    assert len(games) == 0
    assert platforms_list == []


@pytest.mark.asyncio
async def test_platform_filter_with_tab(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Game A", Platform.STEAM),
        _game("epic_1", "Game B", Platform.EPIC),
        _game("gog_1", "Game C", Platform.GOG),
        _game("psn_1", "Game D", Platform.PSN),
    ]
    games, total, _platforms_list = await use_case.execute(
        "uid", tab=LibraryTab.PC, platforms=[Platform.STEAM]
    )

    assert total == 1
    assert len(games) == 1
    assert games[0].platform == Platform.STEAM


@pytest.mark.asyncio
async def test_platform_filter_with_search(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Hades", Platform.STEAM),
        _game("epic_1", "Hades", Platform.EPIC),
        _game("steam_2", "Celeste", Platform.STEAM),
    ]
    games, total, _platforms_list = await use_case.execute(
        "uid", search="hades", platforms=[Platform.STEAM]
    )

    assert total == 1
    assert len(games) == 1
    assert games[0].title == "Hades"
    assert games[0].platform == Platform.STEAM


@pytest.mark.asyncio
async def test_merge_with_platform_filter(use_case: GetLibraryUseCase, repo: AsyncMock) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Elden Ring", Platform.STEAM),
        _game("epic_1", "Elden Ring", Platform.EPIC),
        _game("psn_1", "Elden Ring", Platform.PSN),
    ]
    games, total, platforms_list = await use_case.execute(
        "uid", platforms=[Platform.STEAM, Platform.EPIC]
    )

    assert total == 1
    assert len(games) == 1
    assert games[0].platform == Platform.STEAM
    assert set(platforms_list[0]) == {Platform.STEAM, Platform.EPIC}


@pytest.mark.asyncio
async def test_merge_preserves_order_of_platforms(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("epic_1", "Game A", Platform.EPIC),
        _game("steam_1", "Game A", Platform.STEAM),
        _game("gog_1", "Game A", Platform.GOG),
    ]
    games, total, platforms_list = await use_case.execute("uid")

    assert total == 1
    assert games[0].platform == Platform.STEAM
    assert platforms_list[0] == [Platform.EPIC, Platform.STEAM, Platform.GOG]


@pytest.mark.asyncio
async def test_merge_no_duplicate_platforms_when_same_title_and_platform(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Elden Ring", Platform.STEAM),
        _game("steam_2", "Elden Ring", Platform.STEAM),
        _game("epic_1", "Elden Ring", Platform.EPIC),
    ]
    games, total, platforms_list = await use_case.execute("uid")

    assert total == 1
    assert len(games) == 1
    assert games[0].platform == Platform.STEAM
    assert platforms_list[0] == [Platform.STEAM, Platform.EPIC]


@pytest.mark.asyncio
async def test_merge_no_duplicate_platforms_all_same(
    use_case: GetLibraryUseCase, repo: AsyncMock
) -> None:
    repo.get_games.return_value = [
        _game("steam_1", "Game A", Platform.STEAM),
        _game("steam_2", "Game A", Platform.STEAM),
        _game("steam_3", "Game A", Platform.STEAM),
    ]
    games, total, platforms_list = await use_case.execute("uid")

    assert total == 1
    assert len(games) == 1
    assert platforms_list[0] == [Platform.STEAM]
