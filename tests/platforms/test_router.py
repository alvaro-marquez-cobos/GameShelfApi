"""HTTP router tests for the platforms module."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient

from shared.domain.enums.platform import Platform


def _linked_platform(
    platform: Platform = Platform.STEAM,
    username: str = "steamuser123",
    avatar_url: str | None = "https://cdn.steam.com/avatar.jpg",
    linked_at: str = "2024-01-01T00:00:00+00:00",
) -> SimpleNamespace:
    return SimpleNamespace(
        platform=platform,
        username=username,
        avatar_url=avatar_url,
        linked_at=linked_at,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/platforms
# ---------------------------------------------------------------------------


async def test_get_linked_platforms_returns_list(
    async_client: AsyncClient,
    mock_get_linked_platforms_use_case: AsyncMock,
) -> None:
    mock_get_linked_platforms_use_case.execute = AsyncMock(
        return_value=[
            _linked_platform(),
            _linked_platform(platform=Platform.EPIC, username="epicuser"),
        ]
    )

    response = await async_client.get(
        "/api/v1/platforms",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["platform"] == "steam"
    assert data[0]["username"] == "steamuser123"
    assert data[1]["platform"] == "epic_games"


async def test_get_linked_platforms_empty(
    async_client: AsyncClient,
    mock_get_linked_platforms_use_case: AsyncMock,
) -> None:
    mock_get_linked_platforms_use_case.execute = AsyncMock(return_value=[])

    response = await async_client.get(
        "/api/v1/platforms",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_get_linked_platforms_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/platforms")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/platforms/{platform}
# ---------------------------------------------------------------------------


async def test_unlink_platform_success(
    async_client: AsyncClient,
    mock_unlink_platform_use_case: AsyncMock,
) -> None:
    mock_unlink_platform_use_case.execute = AsyncMock(return_value=None)

    response = await async_client.delete(
        "/api/v1/platforms/steam",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 204


async def test_unlink_platform_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.delete("/api/v1/platforms/steam")
    assert response.status_code == 401


async def test_unlink_platform_invalid_platform(async_client: AsyncClient) -> None:
    response = await async_client.delete(
        "/api/v1/platforms/unknown_platform",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Steam auth URL endpoints
# ---------------------------------------------------------------------------


async def test_steam_auth_url(
    async_client: AsyncClient,
    mock_steam_auth_client: MagicMock,
) -> None:
    response = await async_client.get(
        "/api/v1/platforms/steam/auth-url",
        params={"returnUrl": "myapp://steam/callback"},
    )

    assert response.status_code == 200
    assert "url" in response.json()
    mock_steam_auth_client.build_openid_url.assert_called_once_with("myapp://steam/callback")


async def test_steam_login_url(
    async_client: AsyncClient,
    mock_steam_auth_client: MagicMock,
) -> None:
    response = await async_client.get(
        "/api/v1/platforms/steam/login-url",
        params={"returnUrl": "myapp://steam/callback"},
    )

    assert response.status_code == 200
    assert "url" in response.json()


# ---------------------------------------------------------------------------
# POST /api/v1/platforms/steam/link  (manual by Steam ID)
# ---------------------------------------------------------------------------


async def test_link_steam_manual_success(
    async_client: AsyncClient,
    mock_link_steam_manual_use_case: AsyncMock,
) -> None:
    mock_link_steam_manual_use_case.execute = AsyncMock(return_value=_linked_platform())

    response = await async_client.post(
        "/api/v1/platforms/steam/link",
        headers={"Authorization": "Bearer valid-token"},
        json={"profileUrlOrId": "76561198000000000"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["platform"] == "steam"
    assert data["username"] == "steamuser123"


async def test_link_steam_manual_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/platforms/steam/link",
        json={"profileUrlOrId": "76561198000000000"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/platforms/steam/link/openid
# ---------------------------------------------------------------------------


async def test_link_steam_openid_success(
    async_client: AsyncClient,
    mock_link_steam_use_case: AsyncMock,
) -> None:
    mock_link_steam_use_case.execute = AsyncMock(return_value=_linked_platform())

    response = await async_client.post(
        "/api/v1/platforms/steam/link/openid",
        headers={"Authorization": "Bearer valid-token"},
        json={
            "callbackParams": {"openid.claimed_id": "https://steamcommunity.com/openid/id/12345"}
        },
    )

    assert response.status_code == 201
    assert response.json()["platform"] == "steam"


async def test_link_steam_openid_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/platforms/steam/link/openid",
        json={"callbackParams": {}},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Epic auth URL + link endpoints
# ---------------------------------------------------------------------------


async def test_epic_auth_url(
    async_client: AsyncClient,
    mock_epic_auth_client: MagicMock,
) -> None:
    response = await async_client.get("/api/v1/platforms/epic/auth-url")

    assert response.status_code == 200
    assert "url" in response.json()
    mock_epic_auth_client.build_login_url.assert_called_once()


async def test_link_epic_authcode_success(
    async_client: AsyncClient,
    mock_link_epic_use_case: AsyncMock,
) -> None:
    mock_link_epic_use_case.execute = AsyncMock(
        return_value=_linked_platform(platform=Platform.EPIC, username="epicuser")
    )

    response = await async_client.post(
        "/api/v1/platforms/epic/link/authcode",
        headers={"Authorization": "Bearer valid-token"},
        json={"authCode": "epic-auth-code-abc123"},
    )

    assert response.status_code == 201
    assert response.json()["platform"] == "epic_games"


async def test_link_epic_gdpr_success(
    async_client: AsyncClient,
    mock_link_epic_gdpr_use_case: AsyncMock,
) -> None:
    mock_link_epic_gdpr_use_case.execute = AsyncMock(
        return_value=_linked_platform(platform=Platform.EPIC, username="epicuser")
    )

    response = await async_client.post(
        "/api/v1/platforms/epic/link/gdpr",
        headers={"Authorization": "Bearer valid-token"},
        json={"jsonContent": '{"accountId": "abc123"}'},
    )

    assert response.status_code == 201
    assert response.json()["platform"] == "epic_games"


async def test_link_epic_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/platforms/epic/link",
        json={"code": "some-code"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GOG auth URL + link
# ---------------------------------------------------------------------------


async def test_gog_auth_url(
    async_client: AsyncClient,
    mock_gog_auth_client: MagicMock,
) -> None:
    response = await async_client.get("/api/v1/platforms/gog/auth-url")

    assert response.status_code == 200
    assert "url" in response.json()
    mock_gog_auth_client.build_auth_url.assert_called_once()


async def test_link_gog_success(
    async_client: AsyncClient,
    mock_link_gog_use_case: AsyncMock,
) -> None:
    mock_link_gog_use_case.execute = AsyncMock(
        return_value=_linked_platform(platform=Platform.GOG, username="goguser")
    )

    response = await async_client.post(
        "/api/v1/platforms/gog/link",
        headers={"Authorization": "Bearer valid-token"},
        json={"code": "gog-auth-code-xyz"},
    )

    assert response.status_code == 201
    assert response.json()["platform"] == "gog"


async def test_link_gog_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/platforms/gog/link",
        json={"code": "some-code"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PSN auth URL + link
# ---------------------------------------------------------------------------


async def test_psn_auth_url(
    async_client: AsyncClient,
    mock_psn_auth_client: MagicMock,
) -> None:
    response = await async_client.get("/api/v1/platforms/psn/auth-url")

    assert response.status_code == 200
    assert "url" in response.json()
    mock_psn_auth_client.build_login_url.assert_called_once()


async def test_link_psn_success(
    async_client: AsyncClient,
    mock_link_psn_use_case: AsyncMock,
) -> None:
    mock_link_psn_use_case.execute = AsyncMock(
        return_value=_linked_platform(platform=Platform.PSN, username="psnuser")
    )

    response = await async_client.post(
        "/api/v1/platforms/psn/link",
        headers={"Authorization": "Bearer valid-token"},
        json={"npsso": "npsso-token-abc123"},
    )

    assert response.status_code == 201
    assert response.json()["platform"] == "psn"


async def test_link_psn_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/platforms/psn/link",
        json={"npsso": "some-token"},
    )
    assert response.status_code == 401
