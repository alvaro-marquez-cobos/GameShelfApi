"""HTTP router tests for the settings module."""

from unittest.mock import AsyncMock

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# GET /api/v1/settings/notifications
# ---------------------------------------------------------------------------


async def test_get_notification_prefs_deals_enabled(
    async_client: AsyncClient,
    mock_get_notification_prefs_use_case: AsyncMock,
) -> None:
    mock_get_notification_prefs_use_case.execute = AsyncMock(return_value={"dealsEnabled": True})

    response = await async_client.get(
        "/api/v1/settings/notifications",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["dealsEnabled"] is True


async def test_get_notification_prefs_deals_disabled(
    async_client: AsyncClient,
    mock_get_notification_prefs_use_case: AsyncMock,
) -> None:
    mock_get_notification_prefs_use_case.execute = AsyncMock(return_value={"dealsEnabled": False})

    response = await async_client.get(
        "/api/v1/settings/notifications",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["dealsEnabled"] is False


async def test_get_notification_prefs_missing_key_defaults_false(
    async_client: AsyncClient,
    mock_get_notification_prefs_use_case: AsyncMock,
) -> None:
    mock_get_notification_prefs_use_case.execute = AsyncMock(return_value={})

    response = await async_client.get(
        "/api/v1/settings/notifications",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["dealsEnabled"] is False


async def test_get_notification_prefs_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/settings/notifications")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/v1/settings/notifications
# ---------------------------------------------------------------------------


async def test_update_notification_prefs_success(
    async_client: AsyncClient,
    mock_update_notification_prefs_use_case: AsyncMock,
) -> None:
    mock_update_notification_prefs_use_case.execute = AsyncMock(return_value=None)

    response = await async_client.put(
        "/api/v1/settings/notifications",
        headers={"Authorization": "Bearer valid-token"},
        json={"dealsEnabled": True},
    )

    assert response.status_code == 204


async def test_update_notification_prefs_passes_correct_payload(
    async_client: AsyncClient,
    mock_update_notification_prefs_use_case: AsyncMock,
) -> None:
    mock_update_notification_prefs_use_case.execute = AsyncMock(return_value=None)

    await async_client.put(
        "/api/v1/settings/notifications",
        headers={"Authorization": "Bearer valid-token"},
        json={"dealsEnabled": False},
    )

    mock_update_notification_prefs_use_case.execute.assert_awaited_once_with(
        "test-uid-123", {"dealsEnabled": False}
    )


async def test_update_notification_prefs_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.put(
        "/api/v1/settings/notifications",
        json={"dealsEnabled": True},
    )
    assert response.status_code == 401


async def test_update_notification_prefs_invalid_body(async_client: AsyncClient) -> None:
    response = await async_client.put(
        "/api/v1/settings/notifications",
        headers={"Authorization": "Bearer valid-token"},
        json={"invalid_field": "value"},
    )
    assert response.status_code == 422
