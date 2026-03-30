"""Tests for GetWishlistUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.wishlist.application.get_wishlist_use_case import GetWishlistUseCase
from modules.wishlist.domain.entities.wishlist_item import WishlistItem
from shared.domain.enums.platform import Platform


def _item(game_id: str, title: str) -> WishlistItem:
    return WishlistItem(
        game_id=game_id,
        title=title,
        platform=Platform.STEAM,
        cover_url=None,
        added_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def itad_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock, itad_client: AsyncMock) -> GetWishlistUseCase:
    return GetWishlistUseCase(repo, itad_client)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_items_with_deals(
    use_case: GetWishlistUseCase,
    repo: AsyncMock,
    itad_client: AsyncMock,
) -> None:
    item_a = _item("steam_1", "Hades")
    item_b = _item("steam_2", "Celeste")
    item_c = _item("steam_3", "Unknown Game")
    repo.get_items.return_value = [item_a, item_b, item_c]

    itad_client.lookup_game_ids_batch.return_value = {
        "Hades": "itad-uuid-hades",
        "Celeste": "itad-uuid-celeste",
        "Unknown Game": None,
    }
    fake_deal = {"store": "Steam", "price": 9.99}
    itad_client.get_prices_for_games_batch.return_value = {
        "itad-uuid-hades": [fake_deal],
        "itad-uuid-celeste": [],
    }

    result = await use_case.execute("uid_abc")

    assert len(result) == 3
    assert result[0] == (item_a, [fake_deal])
    assert result[1] == (item_b, [])
    assert result[2] == (item_c, [])  # no ITAD id → no deals


@pytest.mark.asyncio
async def test_empty_wishlist_returns_empty_list(
    use_case: GetWishlistUseCase,
    repo: AsyncMock,
    itad_client: AsyncMock,
) -> None:
    repo.get_items.return_value = []

    result = await use_case.execute("uid_abc")

    assert result == []
    itad_client.lookup_game_ids_batch.assert_not_awaited()


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_itad_id_lookup_failure_returns_empty_deals(
    use_case: GetWishlistUseCase,
    repo: AsyncMock,
    itad_client: AsyncMock,
) -> None:
    repo.get_items.return_value = [_item("steam_1", "Hades")]
    itad_client.lookup_game_ids_batch.side_effect = Exception("ITAD timeout")

    result = await use_case.execute("uid_abc")

    assert len(result) == 1
    item, deals = result[0]
    assert item.game_id == "steam_1"
    assert deals == []


@pytest.mark.asyncio
async def test_itad_price_lookup_failure_returns_empty_deals(
    use_case: GetWishlistUseCase,
    repo: AsyncMock,
    itad_client: AsyncMock,
) -> None:
    repo.get_items.return_value = [_item("steam_1", "Hades")]
    itad_client.lookup_game_ids_batch.return_value = {"Hades": "itad-uuid-hades"}
    itad_client.get_prices_for_games_batch.side_effect = Exception("ITAD price error")

    result = await use_case.execute("uid_abc")

    assert len(result) == 1
    _, deals = result[0]
    assert deals == []
