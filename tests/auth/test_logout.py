from unittest.mock import AsyncMock

import pytest

from modules.auth.application.logout_use_case import LogoutUseCase
from shared.exceptions import UnauthorizedException


async def test_logout_success(
    mock_firebase_auth: AsyncMock,
    mock_token_blacklist: AsyncMock,
) -> None:
    use_case = LogoutUseCase(mock_firebase_auth, mock_token_blacklist)
    await use_case.execute("valid-token")
    mock_token_blacklist.add.assert_called_once()
    call_args = mock_token_blacklist.add.call_args
    token_id = call_args[0][0]
    assert token_id == "test-jti-abc"


async def test_logout_calculates_positive_ttl(
    mock_firebase_auth: AsyncMock,
    mock_token_blacklist: AsyncMock,
) -> None:
    use_case = LogoutUseCase(mock_firebase_auth, mock_token_blacklist)
    await use_case.execute("valid-token")
    call_args = mock_token_blacklist.add.call_args
    ttl = call_args[0][1]
    assert ttl > 0


async def test_logout_invalid_token(
    mock_firebase_auth: AsyncMock,
    mock_token_blacklist: AsyncMock,
) -> None:
    mock_firebase_auth.verify_token = AsyncMock(side_effect=UnauthorizedException("Invalid token"))
    use_case = LogoutUseCase(mock_firebase_auth, mock_token_blacklist)
    with pytest.raises(UnauthorizedException):
        await use_case.execute("bad-token")
    mock_token_blacklist.add.assert_not_called()
