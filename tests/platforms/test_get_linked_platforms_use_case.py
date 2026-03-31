"""Tests for GetLinkedPlatformsUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.platforms.application.get_linked_platforms_use_case import (
    GetLinkedPlatformsUseCase,
)
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock) -> GetLinkedPlatformsUseCase:
    return GetLinkedPlatformsUseCase(repo)


@pytest.mark.asyncio
async def test_returns_linked_platforms(
    repo: AsyncMock, use_case: GetLinkedPlatformsUseCase
) -> None:
    repo.get_linked.return_value = [
        LinkedPlatform(platform=Platform.STEAM, username="gaben"),
        LinkedPlatform(platform=Platform.GOG, username="user_123"),
    ]

    result = await use_case.execute("uid_1")

    assert len(result) == 2
    assert result[0].platform == Platform.STEAM
    repo.get_linked.assert_awaited_once_with("uid_1")


@pytest.mark.asyncio
async def test_returns_empty_list_when_no_platforms(
    repo: AsyncMock, use_case: GetLinkedPlatformsUseCase
) -> None:
    repo.get_linked.return_value = []

    result = await use_case.execute("uid_1")

    assert result == []
