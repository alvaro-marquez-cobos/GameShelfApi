"""Tests for LinkGogUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.platforms.application.link_gog_use_case import LinkGogUseCase
from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from shared.domain.enums.platform import Platform


@pytest.fixture
def gog_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(gog_client: AsyncMock, repo: AsyncMock) -> LinkGogUseCase:
    return LinkGogUseCase(gog_client, repo)


def _make_token(user_id: str = "gog_user_42") -> MagicMock:
    token = MagicMock()
    token.access_token = "acc"
    token.refresh_token = "ref"
    token.user_id = user_id
    token.expires_at = "2099-01-01T00:00:00Z"
    return token


@pytest.mark.asyncio
async def test_links_gog_successfully(
    use_case: LinkGogUseCase, gog_client: AsyncMock, repo: AsyncMock
) -> None:
    gog_client.exchange_code.return_value = _make_token()
    repo.is_linked.return_value = False

    result = await use_case.execute("uid_1", "auth_code_abc")

    assert result.platform == Platform.GOG
    assert result.username == "gog_user_42"
    repo.link.assert_awaited_once()
    repo.store_tokens.assert_awaited_once()
    stored = repo.store_tokens.call_args.args
    assert stored[2]["user_id"] == "gog_user_42"


@pytest.mark.asyncio
async def test_raises_conflict_when_already_linked(
    use_case: LinkGogUseCase, gog_client: AsyncMock, repo: AsyncMock
) -> None:
    gog_client.exchange_code.return_value = _make_token()
    repo.is_linked.return_value = True

    with pytest.raises(PlatformAlreadyLinkedException):
        await use_case.execute("uid_1", "auth_code_abc")

    repo.link.assert_not_awaited()
