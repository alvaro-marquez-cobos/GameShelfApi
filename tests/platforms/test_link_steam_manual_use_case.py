"""Tests for LinkSteamManualUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.platforms.application.link_steam_manual_use_case import LinkSteamManualUseCase
from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.exceptions import BadRequestException


@pytest.fixture
def steam_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(steam_client: AsyncMock, repo: AsyncMock) -> LinkSteamManualUseCase:
    return LinkSteamManualUseCase(steam_client, repo)


@pytest.mark.asyncio
async def test_links_steam_with_steam_id(
    use_case: LinkSteamManualUseCase,
    steam_client: AsyncMock,
    repo: AsyncMock,
) -> None:
    repo.get_linked.return_value = []
    steam_client.get_player_summary.return_value = None

    result = await use_case.execute("uid_1", "76561198000000001")

    assert result.platform == Platform.STEAM
    repo.link.assert_awaited_once()
    repo.store_tokens.assert_awaited_once_with(
        "uid_1", Platform.STEAM, {"steam_id": "76561198000000001"}
    )


@pytest.mark.asyncio
async def test_links_steam_with_vanity_url(
    use_case: LinkSteamManualUseCase, steam_client: AsyncMock, repo: AsyncMock
) -> None:
    repo.get_linked.return_value = []
    steam_client.resolve_vanity_url.return_value = "76561198000000009"
    steam_client.get_player_summary.return_value = None

    await use_case.execute("uid_1", "https://steamcommunity.com/id/gaben")

    steam_client.resolve_vanity_url.assert_awaited_once_with("gaben")


@pytest.mark.asyncio
async def test_raises_when_steam_already_linked(
    use_case: LinkSteamManualUseCase, repo: AsyncMock
) -> None:
    repo.get_linked.return_value = [LinkedPlatform(platform=Platform.STEAM, username="existing")]

    with pytest.raises(PlatformAlreadyLinkedException):
        await use_case.execute("uid_1", "76561198000000001")


@pytest.mark.asyncio
async def test_raises_on_unresolvable_profile(
    use_case: LinkSteamManualUseCase, steam_client: AsyncMock, repo: AsyncMock
) -> None:
    repo.get_linked.return_value = []
    steam_client.resolve_vanity_url.return_value = None

    with pytest.raises(BadRequestException):
        await use_case.execute("uid_1", "bad-profile")
