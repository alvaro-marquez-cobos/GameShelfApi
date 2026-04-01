"""Shared fixtures for platforms HTTP router tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

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
def mock_get_linked_platforms_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_unlink_platform_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_link_steam_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_link_steam_manual_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_link_epic_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_link_epic_gdpr_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_link_gog_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_link_psn_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_steam_auth_client() -> MagicMock:
    mock = MagicMock()
    mock.build_openid_url = MagicMock(return_value="https://steamcommunity.com/openid/login?...")
    return mock


@pytest.fixture
def mock_epic_auth_client() -> MagicMock:
    mock = MagicMock()
    mock.build_login_url = MagicMock(return_value="https://www.epicgames.com/id/authorize?...")
    return mock


@pytest.fixture
def mock_gog_auth_client() -> MagicMock:
    mock = MagicMock()
    mock.build_auth_url = MagicMock(return_value="https://auth.gog.com/auth?...")
    return mock


@pytest.fixture
def mock_psn_auth_client() -> MagicMock:
    mock = MagicMock()
    mock.build_login_url = MagicMock(
        return_value="https://ca.account.sony.com/api/authz/v3/oauth/authorize?..."
    )
    return mock


@pytest.fixture
async def async_client(
    mock_firebase_auth: AsyncMock,
    mock_token_blacklist: AsyncMock,
    mock_get_linked_platforms_use_case: AsyncMock,
    mock_unlink_platform_use_case: AsyncMock,
    mock_link_steam_use_case: AsyncMock,
    mock_link_steam_manual_use_case: AsyncMock,
    mock_link_epic_use_case: AsyncMock,
    mock_link_epic_gdpr_use_case: AsyncMock,
    mock_link_gog_use_case: AsyncMock,
    mock_link_psn_use_case: AsyncMock,
    mock_steam_auth_client: MagicMock,
    mock_epic_auth_client: MagicMock,
    mock_gog_auth_client: MagicMock,
    mock_psn_auth_client: MagicMock,
) -> AsyncGenerator[AsyncClient, None]:
    from composition.dependencies import (
        get_epic_auth_client,
        get_firebase_auth_provider,
        get_get_linked_platforms_use_case,
        get_gog_auth_client,
        get_link_epic_gdpr_use_case,
        get_link_epic_use_case,
        get_link_gog_use_case,
        get_link_psn_use_case,
        get_link_steam_manual_use_case,
        get_link_steam_use_case,
        get_psn_auth_client,
        get_steam_auth_client,
        get_token_blacklist,
        get_unlink_platform_use_case,
    )
    from main import app

    app.dependency_overrides[get_firebase_auth_provider] = lambda: mock_firebase_auth
    app.dependency_overrides[get_token_blacklist] = lambda: mock_token_blacklist
    app.dependency_overrides[get_get_linked_platforms_use_case] = lambda: (
        mock_get_linked_platforms_use_case
    )
    app.dependency_overrides[get_unlink_platform_use_case] = lambda: mock_unlink_platform_use_case
    app.dependency_overrides[get_link_steam_use_case] = lambda: mock_link_steam_use_case
    app.dependency_overrides[get_link_steam_manual_use_case] = lambda: (
        mock_link_steam_manual_use_case
    )
    app.dependency_overrides[get_link_epic_use_case] = lambda: mock_link_epic_use_case
    app.dependency_overrides[get_link_epic_gdpr_use_case] = lambda: mock_link_epic_gdpr_use_case
    app.dependency_overrides[get_link_gog_use_case] = lambda: mock_link_gog_use_case
    app.dependency_overrides[get_link_psn_use_case] = lambda: mock_link_psn_use_case
    app.dependency_overrides[get_steam_auth_client] = lambda: mock_steam_auth_client
    app.dependency_overrides[get_epic_auth_client] = lambda: mock_epic_auth_client
    app.dependency_overrides[get_gog_auth_client] = lambda: mock_gog_auth_client
    app.dependency_overrides[get_psn_auth_client] = lambda: mock_psn_auth_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
