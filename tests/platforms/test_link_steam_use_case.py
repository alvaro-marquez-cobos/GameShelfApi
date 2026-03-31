"""Tests for LinkSteamUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.platforms.application.link_steam_use_case import LinkSteamUseCase
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
def use_case(steam_client: AsyncMock, repo: AsyncMock) -> LinkSteamUseCase:
    return LinkSteamUseCase(steam_client, repo)


_PARAMS = {"openid.claimed_id": "https://steamcommunity.com/openid/id/76561198000000001"}


@pytest.mark.asyncio
async def test_links_steam_successfully(
    use_case: LinkSteamUseCase, steam_client: AsyncMock, repo: AsyncMock
) -> None:
    steam_client.verify_openid.return_value = "76561198000000001"
    repo.get_linked.return_value = []
    player = MagicMock()
    player.persona_name = "GabeN"
    player.avatar_url = "https://img/avatar.jpg"
    steam_client.get_player_summary.return_value = player

    result = await use_case.execute("uid_1", _PARAMS)

    assert result.platform == Platform.STEAM
    assert result.username == "GabeN"
    assert result.avatar_url == "https://img/avatar.jpg"
    repo.link.assert_awaited_once()
    repo.store_tokens.assert_awaited_once()


@pytest.mark.asyncio
async def test_raises_bad_request_when_openid_invalid(
    use_case: LinkSteamUseCase, steam_client: AsyncMock, repo: AsyncMock
) -> None:
    steam_client.verify_openid.return_value = None

    with pytest.raises(BadRequestException):
        await use_case.execute("uid_1", _PARAMS)

    repo.link.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_conflict_when_already_linked(
    use_case: LinkSteamUseCase, steam_client: AsyncMock, repo: AsyncMock
) -> None:
    steam_client.verify_openid.return_value = "76561198000000001"
    repo.get_linked.return_value = [LinkedPlatform(platform=Platform.STEAM, username="existing")]

    with pytest.raises(PlatformAlreadyLinkedException):
        await use_case.execute("uid_1", _PARAMS)

    repo.link.assert_not_awaited()


@pytest.mark.asyncio
async def test_uses_steam_id_as_username_when_player_not_found(
    use_case: LinkSteamUseCase, steam_client: AsyncMock, repo: AsyncMock
) -> None:
    steam_client.verify_openid.return_value = "76561198000000001"
    repo.get_linked.return_value = []
    steam_client.get_player_summary.return_value = None

    result = await use_case.execute("uid_1", _PARAMS)

    assert result.username == "76561198000000001"
    assert result.avatar_url is None
