"""Tests for UnlinkPlatformUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.platforms.application.unlink_platform_use_case import UnlinkPlatformUseCase
from modules.platforms.domain.exceptions import PlatformNotFoundException
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(repo: AsyncMock) -> UnlinkPlatformUseCase:
    return UnlinkPlatformUseCase(repo)


@pytest.mark.asyncio
async def test_unlinks_platform_successfully(
    use_case: UnlinkPlatformUseCase, repo: AsyncMock
) -> None:
    repo.get_linked.return_value = [LinkedPlatform(platform=Platform.STEAM, username="gaben")]

    await use_case.execute("uid_1", Platform.STEAM)

    repo.unlink.assert_awaited_once_with("uid_1", Platform.STEAM)


@pytest.mark.asyncio
async def test_raises_not_found_when_platform_not_linked(
    use_case: UnlinkPlatformUseCase, repo: AsyncMock
) -> None:
    repo.get_linked.return_value = [LinkedPlatform(platform=Platform.EPIC, username="epic_user")]

    with pytest.raises(PlatformNotFoundException):
        await use_case.execute("uid_1", Platform.STEAM)

    repo.unlink.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_not_found_when_no_platforms_linked(
    use_case: UnlinkPlatformUseCase, repo: AsyncMock
) -> None:
    repo.get_linked.return_value = []

    with pytest.raises(PlatformNotFoundException):
        await use_case.execute("uid_1", Platform.GOG)
