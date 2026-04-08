"""Tests for LinkEpicUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.platforms.application.link_epic_use_case import LinkEpicUseCase
from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from shared.domain.enums.platform import Platform


@pytest.fixture
def epic_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(epic_client: AsyncMock, repo: AsyncMock) -> LinkEpicUseCase:
    return LinkEpicUseCase(epic_client, repo)


def _make_token(display_name: str = "EpicUser") -> MagicMock:
    token = MagicMock()
    token.access_token = "acc"
    token.refresh_token = "ref"
    token.account_id = "epic_acc_123"
    token.display_name = display_name
    token.expires_at = "2099-01-01T00:00:00Z"
    return token


@pytest.mark.asyncio
async def test_links_epic_successfully(
    use_case: LinkEpicUseCase, epic_client: AsyncMock, repo: AsyncMock
) -> None:
    epic_client.exchange_auth_code.return_value = _make_token("EpicUser")
    repo.is_linked.return_value = False

    result = await use_case.execute("uid_1", "auth_code_abc")

    assert result.platform == Platform.EPIC
    assert result.username == "EpicUser"
    repo.link.assert_awaited_once()
    repo.store_tokens.assert_awaited_once()
    stored = repo.store_tokens.call_args.args
    assert stored[2]["account_id"] == "epic_acc_123"


@pytest.mark.asyncio
async def test_raises_conflict_when_already_linked(
    use_case: LinkEpicUseCase, epic_client: AsyncMock, repo: AsyncMock
) -> None:
    epic_client.exchange_auth_code.return_value = _make_token()
    repo.is_linked.return_value = True

    with pytest.raises(PlatformAlreadyLinkedException):
        await use_case.execute("uid_1", "auth_code_abc")

    repo.link.assert_not_awaited()


@pytest.mark.asyncio
async def test_falls_back_to_account_id_when_no_display_name(
    use_case: LinkEpicUseCase, epic_client: AsyncMock, repo: AsyncMock
) -> None:
    epic_client.exchange_auth_code.return_value = _make_token(display_name="")
    repo.is_linked.return_value = False

    result = await use_case.execute("uid_1", "auth_code_abc")

    assert result.username == "epic_acc_123"
