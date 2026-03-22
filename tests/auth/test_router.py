from unittest.mock import AsyncMock

from httpx import AsyncClient

from shared.exceptions import UnauthorizedException


async def test_sync_user_success(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/sync",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == "test-uid-123"
    assert data["email"] == "test@example.com"


async def test_sync_user_invalid_token(
    async_client: AsyncClient,
    mock_firebase_auth: AsyncMock,
) -> None:
    mock_firebase_auth.verify_token = AsyncMock(side_effect=UnauthorizedException("Invalid token"))
    response = await async_client.post(
        "/api/v1/auth/sync",
        headers={"Authorization": "Bearer bad-token"},
    )
    assert response.status_code == 401


async def test_sync_user_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post("/api/v1/auth/sync")
    assert response.status_code == 401


async def test_logout_success(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


async def test_logout_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post("/api/v1/auth/logout")
    assert response.status_code == 401


async def test_delete_account_success(async_client: AsyncClient) -> None:
    response = await async_client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 204


async def test_get_profile_success(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == "test-uid-123"


async def test_get_profile_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401
