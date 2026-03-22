from unittest.mock import AsyncMock

import pytest

from modules.auth.application.delete_account_use_case import DeleteAccountUseCase
from modules.auth.domain.exceptions import AccountDeletionException


async def test_delete_account_success(
    mock_cleanup_registry: AsyncMock,
    mock_user_repo: AsyncMock,
    mock_firebase_auth: AsyncMock,
) -> None:
    use_case = DeleteAccountUseCase(mock_cleanup_registry, mock_user_repo, mock_firebase_auth)
    await use_case.execute("test-uid-123")
    mock_cleanup_registry.execute_all.assert_called_once_with("test-uid-123")
    mock_user_repo.delete.assert_called_once_with("test-uid-123")
    mock_firebase_auth.delete_user.assert_called_once_with("test-uid-123")


async def test_delete_account_calls_cleanup_hooks(
    mock_cleanup_registry: AsyncMock,
    mock_user_repo: AsyncMock,
    mock_firebase_auth: AsyncMock,
) -> None:
    use_case = DeleteAccountUseCase(mock_cleanup_registry, mock_user_repo, mock_firebase_auth)
    await use_case.execute("test-uid-123")
    mock_cleanup_registry.execute_all.assert_awaited_once_with("test-uid-123")


async def test_delete_account_firebase_failure_raises(
    mock_cleanup_registry: AsyncMock,
    mock_user_repo: AsyncMock,
    mock_firebase_auth: AsyncMock,
) -> None:
    mock_firebase_auth.delete_user = AsyncMock(side_effect=Exception("Firebase error"))
    use_case = DeleteAccountUseCase(mock_cleanup_registry, mock_user_repo, mock_firebase_auth)
    with pytest.raises(AccountDeletionException):
        await use_case.execute("test-uid-123")
