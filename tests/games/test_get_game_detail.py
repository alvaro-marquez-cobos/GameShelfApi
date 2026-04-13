"""Tests for GetGameDetailUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.games.application.get_game_detail_use_case import GetGameDetailUseCase
from modules.games.domain.entities.hltb import HltbResult
from modules.games.domain.entities.itad import Deal
from modules.games.domain.entities.protondb import ProtonDbRating
from modules.games.domain.entities.steam import SteamAppDetails
from shared.domain.entities.library_game import LibraryGame
from shared.domain.enums.platform import Platform


def _library_game(
    game_id: str = "steam_570",
    title: str = "Dota 2",
    steam_app_id: int | None = 570,
) -> LibraryGame:
    return LibraryGame(
        game_id=game_id,
        title=title,
        platform=Platform.STEAM,
        cover_url=None,
        playtime_minutes=0,
        last_played=None,
        steam_app_id=steam_app_id,
        extra={},
    )


def _steam_details(app_id: int = 570) -> SteamAppDetails:
    return SteamAppDetails(app_id=app_id, name="Dota 2", short_description="MOBA")


def _deal() -> Deal:
    return Deal(
        id="steam-570",
        store_name="Steam",
        price=0.0,
        regular_price=0.0,
        discount=0,
        url="https://store.steampowered.com/app/570",
        currency="USD",
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def steam_metadata() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def protondb() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def hltb() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def itad() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def wishlist_reader() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def library_reader() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    protondb: AsyncMock,
    hltb: AsyncMock,
    itad: AsyncMock,
    wishlist_reader: AsyncMock,
    library_reader: AsyncMock,
) -> GetGameDetailUseCase:
    return GetGameDetailUseCase(
        repo, steam_metadata, protondb, hltb, itad, wishlist_reader, library_reader
    )


# ---------------------------------------------------------------------------
# Happy path — steam_app_id already stored
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_enrichment_when_steam_app_id_known(
    use_case: GetGameDetailUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    protondb: AsyncMock,
    hltb: AsyncMock,
    itad: AsyncMock,
    wishlist_reader: AsyncMock,
    library_reader: AsyncMock,
) -> None:
    library_reader.get_game.return_value = _library_game()
    repo.get_game.return_value = {"game_id": "steam_570", "steam_app_id": 570}
    steam_metadata.get_app_details.return_value = _steam_details()
    protondb.get_compatibility_rating.return_value = ProtonDbRating(
        tier="gold", trending_tier="gold", total=500
    )
    hltb.get_game_duration.return_value = HltbResult(
        main_story=30.0, main_extra=50.0, completionist=100.0
    )
    itad.lookup_game_id_by_steam_app_id.return_value = "itad-uuid"
    itad.get_prices_for_game.return_value = [_deal()]
    wishlist_reader.is_in_wishlist.return_value = True

    result = await use_case.execute("uid_abc", "steam_570")

    assert result.game_id == "steam_570"
    assert result.title == "Dota 2"
    assert result.steam_app_id == 570
    assert result.steam is not None
    assert result.protondb is not None
    assert result.hltb is not None
    assert len(result.deals) == 1
    assert result.is_in_wishlist is True
    hltb.get_game_duration.assert_awaited_once_with("Dota 2")
    # No search_store call needed
    steam_metadata.search_store.assert_not_awaited()


# ---------------------------------------------------------------------------
# Phase 1 — steam_app_id resolved from game_id prefix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_steam_app_id_extracted_from_game_id(
    use_case: GetGameDetailUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    itad: AsyncMock,
    wishlist_reader: AsyncMock,
    library_reader: AsyncMock,
) -> None:
    library_reader.get_game.return_value = None
    repo.get_game.return_value = None  # not in metadata cache
    steam_metadata.get_app_details.return_value = _steam_details()
    itad.lookup_game_id_by_steam_app_id.return_value = None
    wishlist_reader.is_in_wishlist.return_value = False

    result = await use_case.execute("uid_abc", "steam_570")

    assert result.steam_app_id == 570
    assert result.title == "steam_570"
    steam_metadata.search_store.assert_not_awaited()
    repo.update_steam_app_id.assert_awaited_once_with("steam_570", 570)


# ---------------------------------------------------------------------------
# Phase 1 — steam_app_id resolved via search_store fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_steam_app_id_resolved_via_search_store(
    use_case: GetGameDetailUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    itad: AsyncMock,
    wishlist_reader: AsyncMock,
    library_reader: AsyncMock,
) -> None:
    library_reader.get_game.return_value = _library_game(
        game_id="gog_12345", title="Cyberpunk 2077", steam_app_id=None
    )
    repo.get_game.return_value = None
    steam_metadata.search_store.return_value = 1091500  # Cyberpunk
    steam_metadata.get_app_details.return_value = SteamAppDetails(
        app_id=1091500, name="Cyberpunk 2077"
    )
    itad.lookup_game_id_by_steam_app_id.return_value = None
    wishlist_reader.is_in_wishlist.return_value = False

    result = await use_case.execute("uid_abc", "gog_12345")

    assert result.steam_app_id == 1091500
    assert result.title == "Cyberpunk 2077"
    steam_metadata.search_store.assert_awaited_once_with("Cyberpunk 2077")


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_protondb_failure_returns_none_field(
    use_case: GetGameDetailUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    protondb: AsyncMock,
    hltb: AsyncMock,
    itad: AsyncMock,
    wishlist_reader: AsyncMock,
    library_reader: AsyncMock,
) -> None:
    library_reader.get_game.return_value = _library_game()
    repo.get_game.return_value = {"game_id": "steam_570", "steam_app_id": 570}
    steam_metadata.get_app_details.return_value = _steam_details()
    protondb.get_compatibility_rating.side_effect = Exception("ProtonDB unreachable")
    hltb.get_game_duration.return_value = None
    itad.lookup_game_id_by_steam_app_id.return_value = None
    wishlist_reader.is_in_wishlist.return_value = False

    result = await use_case.execute("uid_abc", "steam_570")

    assert result.protondb is None
    assert result.steam is not None


@pytest.mark.asyncio
async def test_all_enrichment_fails_returns_base_data(
    use_case: GetGameDetailUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    protondb: AsyncMock,
    hltb: AsyncMock,
    itad: AsyncMock,
    wishlist_reader: AsyncMock,
    library_reader: AsyncMock,
) -> None:
    library_reader.get_game.return_value = _library_game()
    repo.get_game.return_value = {"game_id": "steam_570", "steam_app_id": 570}
    steam_metadata.get_app_details.side_effect = Exception("Steam down")
    protondb.get_compatibility_rating.side_effect = Exception("ProtonDB down")
    hltb.get_game_duration.side_effect = Exception("HLTB down")
    itad.lookup_game_id_by_steam_app_id.side_effect = Exception("ITAD down")
    wishlist_reader.is_in_wishlist.side_effect = Exception("Firestore down")

    result = await use_case.execute("uid_abc", "steam_570")

    assert result.game_id == "steam_570"
    assert result.steam_app_id == 570
    assert result.steam is None
    assert result.protondb is None
    assert result.hltb is None
    assert result.deals == []
    assert result.is_in_wishlist is False


@pytest.mark.asyncio
async def test_unresolvable_steam_app_id_returns_base_only(
    use_case: GetGameDetailUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    library_reader: AsyncMock,
) -> None:
    library_reader.get_game.return_value = _library_game(
        game_id="gog_99999", title="Unknown Game", steam_app_id=None
    )
    repo.get_game.return_value = None
    steam_metadata.search_store.return_value = None  # not found

    result = await use_case.execute("uid_abc", "gog_99999")

    assert result.steam_app_id is None
    assert result.steam is None
    assert result.deals == []
