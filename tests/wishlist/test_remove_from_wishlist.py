"""Tests for RemoveFromWishlistUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.wishlist.application.remove_from_wishlist_use_case import (
    RemoveFromWishlistUseCase,
)
from modules.wishlist.domain.exceptions import WishlistItemNotFoundException


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock) -> RemoveFromWishlistUseCase:
    return RemoveFromWishlistUseCase(repo)


@pytest.mark.asyncio
async def test_remove_existing_item(
    use_case: RemoveFromWishlistUseCase,
    repo: AsyncMock,
) -> None:
    repo.is_in_wishlist.return_value = True

    await use_case.execute("uid_abc", "steam_570")

    repo.is_in_wishlist.assert_awaited_once_with("uid_abc", "steam_570")
    repo.remove.assert_awaited_once_with("uid_abc", "steam_570")


@pytest.mark.asyncio
async def test_remove_nonexistent_item_raises(
    use_case: RemoveFromWishlistUseCase,
    repo: AsyncMock,
) -> None:
    repo.is_in_wishlist.return_value = False

    with pytest.raises(WishlistItemNotFoundException):
        await use_case.execute("uid_abc", "steam_570")

    repo.remove.assert_not_awaited()
