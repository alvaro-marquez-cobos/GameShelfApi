"""Tests for LinkPsnUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.platforms.application.link_psn_use_case import LinkPsnUseCase
from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


@pytest.fixture
def psn_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(psn_client: AsyncMock, repo: AsyncMock) -> LinkPsnUseCase:
    return LinkPsnUseCase(psn_client, repo)


def _make_token(account_id: str = "psn_user_77") -> MagicMock:
    token = MagicMock()
    token.access_token = "acc"
    token.refresh_token = "ref"
    token.account_id = account_id
    token.expires_at = "2099-01-01T00:00:00Z"
    return token


@pytest.mark.asyncio
async def test_links_psn_successfully(
    use_case: LinkPsnUseCase, psn_client: AsyncMock, repo: AsyncMock
) -> None:
    psn_client.exchange_npsso.return_value = _make_token()
    repo.get_linked.return_value = []

    result = await use_case.execute("uid_1", "npsso_token_abc")

    assert result.platform == Platform.PSN
    assert result.username == "psn_user_77"
    repo.link.assert_awaited_once()
    repo.store_tokens.assert_awaited_once()
    stored = repo.store_tokens.call_args.args
    assert stored[2]["account_id"] == "psn_user_77"


@pytest.mark.asyncio
async def test_raises_conflict_when_already_linked(
    use_case: LinkPsnUseCase, psn_client: AsyncMock, repo: AsyncMock
) -> None:
    psn_client.exchange_npsso.return_value = _make_token()
    repo.get_linked.return_value = [LinkedPlatform(platform=Platform.PSN, username="existing")]

    with pytest.raises(PlatformAlreadyLinkedException):
        await use_case.execute("uid_1", "npsso_token_abc")

    repo.link.assert_not_awaited()
