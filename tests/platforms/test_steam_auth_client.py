"""Tests for SteamAuthClient."""

import httpx
import pytest
import respx

from modules.platforms.domain.entities.steam import SteamGame, SteamPlayer
from modules.platforms.infrastructure.clients.steam_auth_client import SteamAuthClient

_API_KEY = "test-key"
_STEAM_ID = "76561198000000001"


@pytest.fixture
def client() -> SteamAuthClient:
    return SteamAuthClient(api_key=_API_KEY)


# ---------------------------------------------------------------------------
# get_owned_games
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_owned_games_returns_parsed_games(client: SteamAuthClient) -> None:
    payload = {
        "response": {
            "games": [
                {
                    "appid": 570,
                    "name": "Dota 2",
                    "playtime_forever": 1200,
                    "playtime_2weeks": 60,
                    "img_icon_url": "abc123",
                    "rtime_last_played": 1700000000,
                }
            ]
        }
    }
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/IPlayerService/GetOwnedGames/v1/").mock(
            return_value=httpx.Response(200, json=payload)
        )
        games = await client.get_owned_games(_STEAM_ID)

    assert len(games) == 1
    assert isinstance(games[0], SteamGame)
    assert games[0].app_id == 570
    assert games[0].name == "Dota 2"
    assert games[0].playtime_forever == 1200


@pytest.mark.asyncio
async def test_get_owned_games_returns_empty_on_error(client: SteamAuthClient) -> None:
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/IPlayerService/GetOwnedGames/v1/").mock(return_value=httpx.Response(403))
        games = await client.get_owned_games(_STEAM_ID)

    assert games == []


@pytest.mark.asyncio
async def test_get_owned_games_returns_empty_when_no_games(client: SteamAuthClient) -> None:
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/IPlayerService/GetOwnedGames/v1/").mock(
            return_value=httpx.Response(200, json={"response": {}})
        )
        games = await client.get_owned_games(_STEAM_ID)

    assert games == []


# ---------------------------------------------------------------------------
# get_recently_played
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_recently_played_returns_games(client: SteamAuthClient) -> None:
    game = {"appid": 730, "name": "CS:GO", "playtime_forever": 500, "playtime_2weeks": 30}
    payload = {"response": {"games": [game]}}
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/IPlayerService/GetRecentlyPlayedGames/v1/").mock(
            return_value=httpx.Response(200, json=payload)
        )
        games = await client.get_recently_played(_STEAM_ID)

    assert len(games) == 1
    assert games[0].app_id == 730


@pytest.mark.asyncio
async def test_get_recently_played_returns_empty_on_error(client: SteamAuthClient) -> None:
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/IPlayerService/GetRecentlyPlayedGames/v1/").mock(return_value=httpx.Response(500))
        games = await client.get_recently_played(_STEAM_ID)

    assert games == []


# ---------------------------------------------------------------------------
# get_player_summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_player_summary_returns_player(client: SteamAuthClient) -> None:
    payload = {
        "response": {
            "players": [
                {
                    "steamid": _STEAM_ID,
                    "personaname": "GabeN",
                    "avatarfull": "https://cdn.steam.com/avatar.jpg",
                    "profileurl": "https://steamcommunity.com/id/gaben/",
                    "lastlogoff": 1700000000,
                }
            ]
        }
    }
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/ISteamUser/GetPlayerSummaries/v2/").mock(
            return_value=httpx.Response(200, json=payload)
        )
        player = await client.get_player_summary(_STEAM_ID)

    assert isinstance(player, SteamPlayer)
    assert player.persona_name == "GabeN"
    assert player.steam_id == _STEAM_ID


@pytest.mark.asyncio
async def test_get_player_summary_returns_none_when_not_found(client: SteamAuthClient) -> None:
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/ISteamUser/GetPlayerSummaries/v2/").mock(
            return_value=httpx.Response(200, json={"response": {"players": []}})
        )
        player = await client.get_player_summary(_STEAM_ID)

    assert player is None


# ---------------------------------------------------------------------------
# resolve_vanity_url
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_vanity_url_returns_steam_id(client: SteamAuthClient) -> None:
    payload = {"response": {"success": 1, "steamid": _STEAM_ID}}
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/ISteamUser/ResolveVanityURL/v1/").mock(
            return_value=httpx.Response(200, json=payload)
        )
        result = await client.resolve_vanity_url("gaben")

    assert result == _STEAM_ID


@pytest.mark.asyncio
async def test_resolve_vanity_url_returns_none_when_not_found(client: SteamAuthClient) -> None:
    payload = {"response": {"success": 42, "message": "No match"}}
    with respx.mock(base_url="https://api.steampowered.com") as mock:
        mock.get("/ISteamUser/ResolveVanityURL/v1/").mock(
            return_value=httpx.Response(200, json=payload)
        )
        result = await client.resolve_vanity_url("nonexistent")

    assert result is None


# ---------------------------------------------------------------------------
# build_openid_url
# ---------------------------------------------------------------------------


def test_build_openid_url_contains_required_params(client: SteamAuthClient) -> None:
    url = client.build_openid_url("https://myapp.com/callback")
    assert "steamcommunity.com/openid/login" in url
    assert "openid.mode=checkid_setup" in url
    assert "openid.return_to=https" in url


# ---------------------------------------------------------------------------
# verify_openid
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_openid_returns_steam_id_on_success(client: SteamAuthClient) -> None:
    params = {
        "openid.mode": "id_res",
        "openid.claimed_id": f"https://steamcommunity.com/openid/id/{_STEAM_ID}",
        "openid.ns": "http://specs.openid.net/auth/2.0",
    }
    with respx.mock() as mock:
        mock.post("https://steamcommunity.com/openid/login").mock(
            return_value=httpx.Response(200, text="is_valid:true\nns:http://specs.openid.net/auth/2.0\n")
        )
        result = await client.verify_openid(params)

    assert result == _STEAM_ID


@pytest.mark.asyncio
async def test_verify_openid_returns_none_on_invalid(client: SteamAuthClient) -> None:
    params = {
        "openid.mode": "id_res",
        "openid.claimed_id": f"https://steamcommunity.com/openid/id/{_STEAM_ID}",
    }
    with respx.mock() as mock:
        mock.post("https://steamcommunity.com/openid/login").mock(
            return_value=httpx.Response(200, text="is_valid:false\n")
        )
        result = await client.verify_openid(params)

    assert result is None
