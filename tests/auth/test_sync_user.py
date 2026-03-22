from typing import Any
from unittest.mock import AsyncMock

import pytest

from modules.auth.application.sync_user_use_case import SyncUserUseCase
from shared.domain.entities.user import AuthenticatedUser


@pytest.fixture
def auth_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        uid="test-uid-123",
        email="test@example.com",
        display_name="Test User",
        photo_url="https://example.com/photo.jpg",
        is_guest=False,
        provider="google.com",
    )


@pytest.fixture
def guest_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        uid="guest-uid-456",
        email=None,
        display_name=None,
        photo_url=None,
        is_guest=True,
        provider="anonymous",
    )


async def test_sync_new_user(
    mock_user_repo: AsyncMock,
    auth_user: AuthenticatedUser,
    sample_user_data: dict[str, Any],
) -> None:
    use_case = SyncUserUseCase(mock_user_repo)
    result = await use_case.execute(auth_user)
    mock_user_repo.upsert.assert_called_once_with(auth_user)
    assert result == sample_user_data


async def test_sync_guest_user(
    mock_user_repo: AsyncMock,
    guest_user: AuthenticatedUser,
) -> None:
    guest_data = {
        "uid": "guest-uid-456",
        "email": None,
        "display_name": None,
        "photo_url": None,
        "is_guest": True,
        "provider": "anonymous",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    mock_user_repo.upsert = AsyncMock(return_value=guest_data)
    use_case = SyncUserUseCase(mock_user_repo)
    result = await use_case.execute(guest_user)
    assert result["is_guest"] is True
    assert result["provider"] == "anonymous"
