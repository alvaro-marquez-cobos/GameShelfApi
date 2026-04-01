"""HTTP router tests for the games module."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from httpx import AsyncClient


def _game_detail(
    with_proton: bool = True,
    with_hltb: bool = True,
    with_steam: bool = True,
    with_deals: bool = True,
    in_wishlist: bool = False,
) -> SimpleNamespace:
    protondb = (
        SimpleNamespace(tier="gold", trending_tier="gold", total=500) if with_proton else None
    )
    hltb = (
        SimpleNamespace(main_story=30.0, main_extra=50.0, completionist=100.0)
        if with_hltb
        else None
    )
    steam = (
        SimpleNamespace(
            genres=["Action", "Strategy"],
            developers=["Valve"],
            publishers=["Valve"],
            release_date="2013-07-09",
            metacritic_score=90,
            recommendation_count=1_000_000,
            screenshots=["https://cdn.steam.com/screenshot1.jpg"],
        )
        if with_steam
        else None
    )
    deals = (
        [
            SimpleNamespace(
                id="steam-570",
                store_name="Steam",
                price=0.0,
                regular_price=0.0,
                discount=0,
                url="https://store.steampowered.com/app/570",
                currency="USD",
            )
        ]
        if with_deals
        else []
    )
    return SimpleNamespace(
        game_id="steam_570",
        title="Dota 2",
        steam_app_id=570,
        protondb=protondb,
        hltb=hltb,
        steam=steam,
        deals=deals,
        is_in_wishlist=in_wishlist,
    )


def _dlcs() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            app_id=123456,
            name="Dota 2 Plus",
            header_image="https://cdn.steam.com/dlc.jpg",
            is_owned=True,
        ),
        SimpleNamespace(
            app_id=789012,
            name="Dota 2 Battle Pass",
            header_image="https://cdn.steam.com/bp.jpg",
            is_owned=False,
        ),
    ]


# ---------------------------------------------------------------------------
# GET /api/v1/games/{game_id}
# ---------------------------------------------------------------------------


async def test_get_game_detail_full_enrichment(
    async_client: AsyncClient,
    mock_get_game_detail_use_case: AsyncMock,
) -> None:
    mock_get_game_detail_use_case.execute = AsyncMock(return_value=_game_detail())

    response = await async_client.get(
        "/api/v1/games/steam_570",
        headers={"Authorization": "Bearer valid-token"},
        params={"title": "Dota 2"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["game"]["id"] == "steam_570"
    assert data["game"]["steamAppId"] == 570
    assert data["protonDb"]["tier"] == "gold"
    assert data["howLongToBeat"]["mainHours"] == 30.0
    assert data["steamMetadata"]["metacriticScore"] == 90
    assert len(data["deals"]) == 1
    assert data["isInWishlist"] is False


async def test_get_game_detail_graceful_degradation(
    async_client: AsyncClient,
    mock_get_game_detail_use_case: AsyncMock,
) -> None:
    mock_get_game_detail_use_case.execute = AsyncMock(
        return_value=_game_detail(
            with_proton=False, with_hltb=False, with_steam=False, with_deals=False
        )
    )

    response = await async_client.get(
        "/api/v1/games/steam_570",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["protonDb"] is None
    assert data["howLongToBeat"] is None
    assert data["steamMetadata"] is None
    assert data["deals"] == []


async def test_get_game_detail_in_wishlist(
    async_client: AsyncClient,
    mock_get_game_detail_use_case: AsyncMock,
) -> None:
    mock_get_game_detail_use_case.execute = AsyncMock(return_value=_game_detail(in_wishlist=True))

    response = await async_client.get(
        "/api/v1/games/steam_570",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["isInWishlist"] is True


async def test_get_game_detail_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/games/steam_570")
    assert response.status_code == 401


async def test_get_game_detail_uses_title_query_param(
    async_client: AsyncClient,
    mock_get_game_detail_use_case: AsyncMock,
) -> None:
    mock_get_game_detail_use_case.execute = AsyncMock(return_value=_game_detail())

    await async_client.get(
        "/api/v1/games/steam_570",
        headers={"Authorization": "Bearer valid-token"},
        params={"title": "Dota 2"},
    )

    mock_get_game_detail_use_case.execute.assert_awaited_once_with(
        "test-uid-123", "steam_570", "Dota 2"
    )


async def test_get_game_detail_falls_back_to_game_id_when_no_title(
    async_client: AsyncClient,
    mock_get_game_detail_use_case: AsyncMock,
) -> None:
    mock_get_game_detail_use_case.execute = AsyncMock(return_value=_game_detail())

    await async_client.get(
        "/api/v1/games/steam_570",
        headers={"Authorization": "Bearer valid-token"},
    )

    mock_get_game_detail_use_case.execute.assert_awaited_once_with(
        "test-uid-123", "steam_570", "steam_570"
    )


# ---------------------------------------------------------------------------
# GET /api/v1/games/{game_id}/dlcs
# ---------------------------------------------------------------------------


async def test_get_game_dlcs_success(
    async_client: AsyncClient,
    mock_get_game_dlcs_use_case: AsyncMock,
) -> None:
    mock_get_game_dlcs_use_case.execute = AsyncMock(return_value=_dlcs())

    response = await async_client.get(
        "/api/v1/games/steam_570/dlcs",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["dlcs"]) == 2
    assert data["dlcs"][0]["appId"] == 123456
    assert data["dlcs"][0]["name"] == "Dota 2 Plus"
    assert data["dlcs"][0]["isOwned"] is True
    assert data["dlcs"][1]["isOwned"] is False


async def test_get_game_dlcs_empty(
    async_client: AsyncClient,
    mock_get_game_dlcs_use_case: AsyncMock,
) -> None:
    mock_get_game_dlcs_use_case.execute = AsyncMock(return_value=[])

    response = await async_client.get(
        "/api/v1/games/steam_570/dlcs",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["dlcs"] == []


async def test_get_game_dlcs_no_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/games/steam_570/dlcs")
    assert response.status_code == 401
