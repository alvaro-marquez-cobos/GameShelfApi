"""Shared fixtures for home HTTP router tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_firebase_auth() -> AsyncMock:
    mock = AsyncMock()
    mock.verify_token = AsyncMock(
        return_value={
            "uid": "test-uid-123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
            "iat": 1700000000,
            "exp": 9999999999,
            "jti": "test-jti-abc",
            "firebase": {"sign_in_provider": "google.com"},
        }
    )
    return mock


@pytest.fixture
def mock_token_blacklist() -> AsyncMock:
    mock = AsyncMock()
    mock.is_blacklisted = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def mock_get_home_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
async def async_client(
    mock_firebase_auth: AsyncMock,
    mock_token_blacklist: AsyncMock,
    mock_get_home_use_case: AsyncMock,
) -> AsyncGenerator[AsyncClient, None]:
    from composition.dependencies import (
        get_firebase_auth_provider,
        get_get_home_use_case,
        get_token_blacklist,
    )
    from main import app

    app.dependency_overrides[get_firebase_auth_provider] = lambda: mock_firebase_auth
    app.dependency_overrides[get_token_blacklist] = lambda: mock_token_blacklist
    app.dependency_overrides[get_get_home_use_case] = lambda: mock_get_home_use_case

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
