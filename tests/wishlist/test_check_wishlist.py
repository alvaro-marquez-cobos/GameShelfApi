"""Tests for CheckWishlistUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.wishlist.application.check_wishlist_use_case import CheckWishlistUseCase


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock) -> CheckWishlistUseCase:
    return CheckWishlistUseCase(repo)


@pytest.mark.asyncio
async def test_returns_true_when_in_wishlist(
    use_case: CheckWishlistUseCase,
    repo: AsyncMock,
) -> None:
    repo.is_in_wishlist.return_value = True

    result = await use_case.execute("uid_abc", "steam_570")

    assert result is True
    repo.is_in_wishlist.assert_awaited_once_with("uid_abc", "steam_570")


@pytest.mark.asyncio
async def test_returns_false_when_not_in_wishlist(
    use_case: CheckWishlistUseCase,
    repo: AsyncMock,
) -> None:
    repo.is_in_wishlist.return_value = False

    result = await use_case.execute("uid_abc", "steam_999")

    assert result is False
