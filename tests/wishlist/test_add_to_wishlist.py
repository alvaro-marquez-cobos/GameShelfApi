"""Tests for AddToWishlistUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.wishlist.application.add_to_wishlist_use_case import AddToWishlistUseCase
from modules.wishlist.domain.entities.wishlist_item import WishlistItem
from modules.wishlist.domain.exceptions import WishlistItemAlreadyExistsException
from shared.domain.enums.platform import Platform


def _item(game_id: str = "steam_570") -> WishlistItem:
    return WishlistItem(
        game_id=game_id,
        title="Dota 2",
        platform=Platform.STEAM,
        cover_url=None,
        added_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock) -> AddToWishlistUseCase:
    return AddToWishlistUseCase(repo)


@pytest.mark.asyncio
async def test_add_new_item_calls_repo(
    use_case: AddToWishlistUseCase,
    repo: AsyncMock,
) -> None:
    repo.is_in_wishlist.return_value = False
    item = _item()

    await use_case.execute("uid_abc", item)

    repo.is_in_wishlist.assert_awaited_once_with("uid_abc", item.game_id)
    repo.add.assert_awaited_once_with("uid_abc", item)


@pytest.mark.asyncio
async def test_add_duplicate_raises_exception(
    use_case: AddToWishlistUseCase,
    repo: AsyncMock,
) -> None:
    repo.is_in_wishlist.return_value = True
    item = _item()

    with pytest.raises(WishlistItemAlreadyExistsException):
        await use_case.execute("uid_abc", item)

    repo.add.assert_not_awaited()
