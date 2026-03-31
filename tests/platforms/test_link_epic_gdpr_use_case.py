"""Tests for LinkEpicGdprUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.platforms.application.link_epic_gdpr_use_case import LinkEpicGdprUseCase
from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.exceptions import BadRequestException


def _epic_game(namespace: str, app_name: str, catalog_item_id: str) -> MagicMock:
    game = MagicMock()
    game.namespace = namespace
    game.app_name = app_name
    game.catalog_item_id = catalog_item_id
    return game


@pytest.fixture
def epic_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def platform_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def library_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    epic_client: AsyncMock,
    platform_repo: AsyncMock,
    library_repo: AsyncMock,
) -> LinkEpicGdprUseCase:
    return LinkEpicGdprUseCase(epic_client, platform_repo, library_repo)


@pytest.mark.asyncio
async def test_links_epic_with_gdpr_import(
    use_case: LinkEpicGdprUseCase,
    epic_client: AsyncMock,
    platform_repo: AsyncMock,
    library_repo: AsyncMock,
) -> None:
    platform_repo.get_linked.return_value = []
    epic_client.parse_gdpr_export = MagicMock(return_value=[_epic_game("fn", "Fortnite", "cat_1")])

    result = await use_case.execute("uid_1", "{}")

    assert result.platform == Platform.EPIC
    assert result.username == "imported"
    library_repo.upsert_games.assert_awaited_once()
    platform_repo.link.assert_awaited_once()


@pytest.mark.asyncio
async def test_raises_when_epic_already_linked(
    use_case: LinkEpicGdprUseCase,
    platform_repo: AsyncMock,
) -> None:
    platform_repo.get_linked.return_value = [LinkedPlatform(platform=Platform.EPIC, username="u")]

    with pytest.raises(PlatformAlreadyLinkedException):
        await use_case.execute("uid_1", "{}")


@pytest.mark.asyncio
async def test_raises_when_no_games_in_export(
    use_case: LinkEpicGdprUseCase,
    epic_client: AsyncMock,
    platform_repo: AsyncMock,
) -> None:
    platform_repo.get_linked.return_value = []
    epic_client.parse_gdpr_export = MagicMock(return_value=[])

    with pytest.raises(BadRequestException):
        await use_case.execute("uid_1", "{}")
