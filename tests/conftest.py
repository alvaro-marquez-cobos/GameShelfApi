import os
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("API_ENV", "testing")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("FIREBASE_PRIVATE_KEY", "test-key")
os.environ.setdefault("FIREBASE_CLIENT_EMAIL", "test@test.iam.gserviceaccount.com")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
def sample_decoded_token() -> dict[str, Any]:
    return {
        "uid": "test-uid-123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "iat": 1700000000,
        "exp": 9999999999,
        "jti": "test-jti-abc",
        "firebase": {"sign_in_provider": "google.com"},
    }


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    return {
        "uid": "test-uid-123",
        "email": "test@example.com",
        "display_name": "Test User",
        "photo_url": "https://example.com/photo.jpg",
        "is_guest": False,
        "provider": "google.com",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }


@pytest.fixture
def mock_firebase_auth(sample_decoded_token: dict[str, Any]) -> AsyncMock:
    mock = AsyncMock()
    mock.verify_token = AsyncMock(return_value=sample_decoded_token)
    mock.delete_user = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_user_repo(sample_user_data: dict[str, Any]) -> AsyncMock:
    mock = AsyncMock()
    mock.find_by_uid = AsyncMock(return_value=sample_user_data)
    mock.upsert = AsyncMock(return_value=sample_user_data)
    mock.delete = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_token_blacklist() -> AsyncMock:
    mock = AsyncMock()
    mock.add = AsyncMock(return_value=None)
    mock.is_blacklisted = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def mock_cleanup_registry() -> AsyncMock:
    mock = AsyncMock()
    mock.register = MagicMock(return_value=None)
    mock.execute_all = AsyncMock(return_value=None)
    return mock


@pytest.fixture
async def async_client(
    mock_firebase_auth: AsyncMock,
    mock_token_blacklist: AsyncMock,
    mock_user_repo: AsyncMock,
    mock_cleanup_registry: AsyncMock,
) -> AsyncGenerator[AsyncClient, None]:
    from composition.dependencies import (
        get_cleanup_registry,
        get_firebase_auth_provider,
        get_token_blacklist,
        get_user_repository,
    )
    from main import app

    app.dependency_overrides[get_firebase_auth_provider] = lambda: mock_firebase_auth
    app.dependency_overrides[get_token_blacklist] = lambda: mock_token_blacklist
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repo
    app.dependency_overrides[get_cleanup_registry] = lambda: mock_cleanup_registry

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
