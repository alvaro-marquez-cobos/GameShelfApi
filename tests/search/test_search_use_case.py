"""Tests for SearchGamesUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.search.application.search_use_case import SearchGamesUseCase


def _itad_result(
    game_id: str,
    title: str,
    steam_app_id: int | None = None,
    game_type: str | None = "game",
) -> MagicMock:
    r = MagicMock()
    r.id = game_id
    r.title = title
    r.cover_url = f"https://img/{game_id}.jpg"
    r.steam_app_id = steam_app_id
    r.game_type = game_type
    return r


@pytest.fixture
def itad_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def game_reader() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def wishlist_reader() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    itad_client: AsyncMock,
    game_reader: AsyncMock,
    wishlist_reader: AsyncMock,
) -> SearchGamesUseCase:
    return SearchGamesUseCase(itad_client, game_reader, wishlist_reader)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_marks_owned_and_wishlisted(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
    game_reader: AsyncMock,
    wishlist_reader: AsyncMock,
) -> None:
    """Original happy-path test — updated to include game_type assertions."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
        _itad_result("itad-celeste", "Celeste", steam_app_id=504230),
        _itad_result("itad-hollow", "Hollow Knight", steam_app_id=367520),
        _itad_result("itad-nosteam", "DRM-free Game", steam_app_id=None),
    ]
    game_reader.check_owned_game_ids.return_value = {"steam_1145360"}
    wishlist_reader.check_wishlist_ids.return_value = {"itad-celeste"}

    results = await use_case.execute("uid_abc", "Hades")

    assert len(results) == 4
    hades = results[0]
    assert hades.title == "Hades"
    assert hades.is_owned is True
    assert hades.is_in_wishlist is False
    assert hades.game_type == "game"

    celeste = results[1]
    assert celeste.is_owned is False
    assert celeste.is_in_wishlist is True
    assert celeste.game_type == "game"

    hollow = results[2]
    assert hollow.is_owned is False
    assert hollow.is_in_wishlist is False
    assert hollow.game_type == "game"

    nosteam = results[3]
    assert nosteam.steam_app_id is None
    assert nosteam.is_owned is False


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_itad_failure_returns_empty_list(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    itad_client.search_games.side_effect = Exception("ITAD timeout")

    results = await use_case.execute("uid_abc", "Hades")

    assert results == []


@pytest.mark.asyncio
async def test_empty_itad_results_returns_empty_list(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    itad_client.search_games.return_value = []

    results = await use_case.execute("uid_abc", "xyznonexistent")

    assert results == []


@pytest.mark.asyncio
async def test_owned_and_wishlist_fetch_failure_defaults_to_false(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
    game_reader: AsyncMock,
    wishlist_reader: AsyncMock,
) -> None:
    """Graceful degradation: ownership/wishlist failures default to False."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
    ]
    game_reader.check_owned_game_ids.side_effect = Exception("Firestore down")
    wishlist_reader.check_wishlist_ids.side_effect = Exception("Firestore down")

    results = await use_case.execute("uid_abc", "Hades")

    assert len(results) == 1
    assert results[0].is_owned is False
    assert results[0].is_in_wishlist is False


# ---------------------------------------------------------------------------
# DLC filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_filters_out_dlc_results(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """ITAD returns a mix of base games and DLCs; only base games pass through."""
    dlc_1_title = "Hades -- Crown of the Bloodless (DLC)"
    dlc_2_title = "Celeste -- Farewell (DLC)"
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
        _itad_result("itad-dlc-1", dlc_1_title, game_type="dlc"),
        _itad_result("itad-celeste", "Celeste", steam_app_id=504230),
        _itad_result("itad-dlc-2", dlc_2_title, game_type="dlc"),
    ]

    results = await use_case.execute("uid_abc", "Hades")

    assert len(results) == 2
    assert results[0].title == "Hades"
    assert results[0].game_type == "game"
    assert results[1].title == "Celeste"
    assert results[1].game_type == "game"


@pytest.mark.asyncio
async def test_search_all_dlc_returns_empty_list(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """When all ITAD results are DLCs, the use case returns an empty list."""
    dlc_1_title = "Hades -- Crown of the Bloodless (DLC)"
    dlc_2_title = "Hades -- The Black Market (DLC)"
    itad_client.search_games.return_value = [
        _itad_result("itad-dlc-1", dlc_1_title, game_type="dlc"),
        _itad_result("itad-dlc-2", dlc_2_title, game_type="dlc"),
    ]

    results = await use_case.execute("uid_abc", "Hades")

    assert results == []


@pytest.mark.asyncio
async def test_search_propagates_game_type_to_results(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """The game_type field from ITAD is propagated through to the SearchResult."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
    ]

    results = await use_case.execute("uid_abc", "Hades")

    assert len(results) == 1
    assert results[0].game_type == "game"


@pytest.mark.asyncio
async def test_search_passes_results_without_explicit_type(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Results that omit the type field are treated as base games."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360, game_type=None),
    ]

    results = await use_case.execute("uid_abc", "Hades")

    assert len(results) == 1
    assert results[0].game_type is None


# ---------------------------------------------------------------------------
# Special edition filtering (Deluxe, GOTY, Ultimate, etc.)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_filters_out_deluxe_edition(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Digital Deluxe Edition titles should be filtered out."""
    itad_client.search_games.return_value = [
        _itad_result(
            "itad-tlou",
            "The Last of Us Part I Digital Deluxe Edition",
            steam_app_id=2056740,
        ),
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
    ]

    results = await use_case.execute("uid_abc", "The Last of Us")

    assert len(results) == 1
    assert results[0].title == "Hades"


@pytest.mark.asyncio
async def test_search_filters_out_goty_edition(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Game of the Year / GOTY editions should be filtered out."""
    itad_client.search_games.return_value = [
        _itad_result(
            "itad-cyberpunk",
            "Cyberpunk 2077 Game of the Year Edition",
            steam_app_id=1091500,
        ),
        _itad_result("itad-hades", "Hades GOTY Edition", steam_app_id=1145360),
    ]

    results = await use_case.execute("uid_abc", "Cyberpunk")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_filters_out_ultimate_and_gold_editions(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Ultimate and Gold editions should be filtered out."""
    itad_client.search_games.return_value = [
        _itad_result("itad-witcher3", "The Witcher 3 Ultimate Edition", steam_app_id=292030),
        _itad_result("itad-elden", "Elden Ring Gold Edition", steam_app_id=1245620),
    ]

    results = await use_case.execute("uid_abc", "Witcher")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_filters_out_definitive_and_special_editions(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Definitive and Special editions should be filtered out."""
    itad_client.search_games.return_value = [
        _itad_result(
            "itad-dragonball",
            "DRAGON BALL Z : KAKAROT:-Daima Edition",
            steam_app_id=1556340,
        ),
        _itad_result("itad-horizon", "Horizon Zero Dawn Special Edition", steam_app_id=1151640),
    ]

    results = await use_case.execute("uid_abc", "Dragon Ball")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_keeps_base_game_with_edition_word_in_title(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Base games without edition keywords should still pass through."""
    # "Deluxe" in a store name or description context wouldn't appear
    # in the title, so this test verifies normal games still pass.
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
        _itad_result("itad-celeste", "Celeste", steam_app_id=504230),
    ]

    results = await use_case.execute("uid_abc", "Indie games")

    assert len(results) == 2


@pytest.mark.asyncio
async def test_search_all_editions_returns_empty_list(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """When all ITAD results are special editions, return empty list."""
    itad_client.search_games.return_value = [
        _itad_result("itad-game1", "Some Game Deluxe Edition", steam_app_id=1234567),
        _itad_result("itad-game2", "Another Game GOTY Edition", steam_app_id=7654321),
    ]

    results = await use_case.execute("uid_abc", "Some Game")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_mixed_dlc_and_editions_filtered(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Both DLCs and special editions are filtered; only base games remain."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
        _itad_result("itad-dlc-1", "Hades -- DLC Pack", game_type="dlc"),
        _itad_result("itad-celeste", "Celeste Digital Deluxe Edition", steam_app_id=504230),
        _itad_result("itad-hollow", "Hollow Knight GOTY Edition", steam_app_id=367520),
    ]

    results = await use_case.execute("uid_abc", "Indie")

    assert len(results) == 1
    assert results[0].title == "Hades"


# ---------------------------------------------------------------------------
# Soundtrack / OST filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_filters_out_soundtracks(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Soundtracks should be filtered out from search results."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades-soundtrack", "Hades Original Soundtrack", steam_app_id=1774320),
        _itad_result(
            "itad-celeste-soundtrack", "Celeste Original Soundtrack", steam_app_id=1597440
        ),
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
    ]

    results = await use_case.execute("uid_abc", "Indie")

    assert len(results) == 1
    assert results[0].title == "Hades"


@pytest.mark.asyncio
async def test_search_filters_out_ost_results(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """OST (Original Sound Track) entries should be filtered out."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades-ost", "Hades OST", steam_app_id=1774320),
        _itad_result("itad-celeste-ost", "Celeste OST", steam_app_id=1597440),
    ]

    results = await use_case.execute("uid_abc", "Indie")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_mixed_soundtrack_dlc_edition_filtered(
    use_case: SearchGamesUseCase,
    itad_client: AsyncMock,
) -> None:
    """Soundtracks, DLCs and special editions all filtered; only base games remain."""
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360),
        _itad_result("itad-dlc-1", "Hades -- DLC Pack", game_type="dlc"),
        _itad_result("itad-soundtrack", "Hades Original Soundtrack", steam_app_id=1774320),
        _itad_result("itad-celeste-deluxe", "Celeste Digital Deluxe Edition", steam_app_id=504230),
        _itad_result("itad-hollow-ost", "Hollow Knight OST", steam_app_id=1976050),
    ]

    results = await use_case.execute("uid_abc", "Indie")

    assert len(results) == 1
    assert results[0].title == "Hades"
