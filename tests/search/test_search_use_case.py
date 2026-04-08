"""Tests for SearchGamesUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.search.application.search_use_case import SearchGamesUseCase


def _itad_result(game_id: str, title: str, steam_app_id: int | None = None) -> MagicMock:
    r = MagicMock()
    r.id = game_id
    r.title = title
    r.cover_url = f"https://img/{game_id}.jpg"
    r.steam_app_id = steam_app_id
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

    celeste = results[1]
    assert celeste.is_owned is False
    assert celeste.is_in_wishlist is True

    hollow = results[2]
    assert hollow.is_owned is False
    assert hollow.is_in_wishlist is False

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
    itad_client.search_games.return_value = [
        _itad_result("itad-hades", "Hades", steam_app_id=1145360)
    ]
    game_reader.check_owned_game_ids.side_effect = Exception("Firestore down")
    wishlist_reader.check_wishlist_ids.side_effect = Exception("Firestore down")

    results = await use_case.execute("uid_abc", "Hades")

    assert len(results) == 1
    assert results[0].is_owned is False
    assert results[0].is_in_wishlist is False
