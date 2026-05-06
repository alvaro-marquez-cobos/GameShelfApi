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


# ---------------------------------------------------------------------------
# POST /api/v1/settings/push-tokens
# ---------------------------------------------------------------------------


async def test_register_push_token_success(
    async_client: AsyncClient,
    mock_settings_repository: AsyncMock,
) -> None:
    mock_settings_repository.register_push_token = AsyncMock(return_value="ios_abc123")

    response = await async_client.post(
        "/api/v1/settings/push-tokens",
        headers={"Authorization": "Bearer valid-token"},
        json={"expo_token": "ExponentPushToken[xxx]", "platform": "ios"},
    )

    assert response.status_code == 200
    assert response.json()["tokenId"] == "ios_abc123"


async def test_register_push_token_passes_correct_args(
    async_client: AsyncClient,
    mock_settings_repository: AsyncMock,
) -> None:
    mock_settings_repository.register_push_token = AsyncMock(return_value="android_def456")

    await async_client.post(
        "/api/v1/settings/push-tokens",
        headers={"Authorization": "Bearer valid-token"},
        json={"expo_token": "ExponentPushToken[yyy]", "platform": "android"},
    )

    mock_settings_repository.register_push_token.assert_awaited_once_with(
        uid="test-uid-123",
        expo_token="ExponentPushToken[yyy]",
        platform="android",
    )


async def test_register_push_token_invalid_platform(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/settings/push-tokens",
        headers={"Authorization": "Bearer valid-token"},
        json={"expo_token": "ExponentPushToken[xxx]", "platform": "windows"},
    )
    assert response.status_code == 422


async def test_register_push_token_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/settings/push-tokens",
        json={"expo_token": "ExponentPushToken[xxx]", "platform": "ios"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/settings/push-tokens  (bulk)
# ---------------------------------------------------------------------------


async def test_remove_all_push_tokens_success(
    async_client: AsyncClient,
    mock_settings_repository: AsyncMock,
) -> None:
    mock_settings_repository.remove_all_push_tokens = AsyncMock(return_value=None)

    response = await async_client.delete(
        "/api/v1/settings/push-tokens",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 204
    mock_settings_repository.remove_all_push_tokens.assert_awaited_once_with(uid="test-uid-123")


async def test_remove_all_push_tokens_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.delete("/api/v1/settings/push-tokens")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/settings/push-tokens/{token_id}
# ---------------------------------------------------------------------------


async def test_remove_push_token_success(
    async_client: AsyncClient,
    mock_settings_repository: AsyncMock,
) -> None:
    mock_settings_repository.remove_push_token = AsyncMock(return_value=None)

    response = await async_client.delete(
        "/api/v1/settings/push-tokens/ios_abc123",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 204
    mock_settings_repository.remove_push_token.assert_awaited_once_with(
        uid="test-uid-123", token_id="ios_abc123"
    )


async def test_remove_push_token_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.delete("/api/v1/settings/push-tokens/ios_abc123")
    assert response.status_code == 401
