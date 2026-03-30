"""Tests for GetGameDlcsUseCase."""

from unittest.mock import AsyncMock

import pytest

from modules.games.application.get_game_dlcs_use_case import GetGameDlcsUseCase
from modules.games.domain.entities.steam import SteamAppDetails


def _dlc_details(app_id: int, name: str) -> SteamAppDetails:
    return SteamAppDetails(app_id=app_id, name=name, header_image=f"http://img/{app_id}.jpg")


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def steam_metadata() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def game_reader() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    game_reader: AsyncMock,
) -> GetGameDlcsUseCase:
    return GetGameDlcsUseCase(repo, steam_metadata, game_reader)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_dlcs_with_ownership_flags(
    use_case: GetGameDlcsUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    game_reader: AsyncMock,
) -> None:
    repo.get_game.return_value = {"game_id": "steam_570", "steam_app_id": 570}
    base_game = SteamAppDetails(app_id=570, name="Dota 2", dlc_app_ids=[100, 200, 300])
    steam_metadata.get_app_details.side_effect = [
        base_game,
        _dlc_details(100, "DLC A"),
        _dlc_details(200, "DLC B"),
        _dlc_details(300, "DLC C"),
    ]
    game_reader.get_owned_game_ids.return_value = {"steam_570", "steam_100"}

    result = await use_case.execute("uid_abc", "steam_570")

    assert len(result) == 3
    assert result[0].app_id == 100
    assert result[0].is_owned is True
    assert result[1].app_id == 200
    assert result[1].is_owned is False
    assert result[2].app_id == 300
    assert result[2].is_owned is False


@pytest.mark.asyncio
async def test_one_dlc_fetch_fails_others_returned(
    use_case: GetGameDlcsUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    game_reader: AsyncMock,
) -> None:
    repo.get_game.return_value = {"game_id": "steam_570", "steam_app_id": 570}
    base_game = SteamAppDetails(app_id=570, name="Dota 2", dlc_app_ids=[100, 200])
    steam_metadata.get_app_details.side_effect = [
        base_game,
        Exception("Steam API error"),
        _dlc_details(200, "DLC B"),
    ]
    game_reader.get_owned_game_ids.return_value = set()

    result = await use_case.execute("uid_abc", "steam_570")

    assert len(result) == 1
    assert result[0].app_id == 200


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_steam_app_id_returns_empty(
    use_case: GetGameDlcsUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
) -> None:
    repo.get_game.return_value = {"game_id": "gog_12345"}  # no steam_app_id

    result = await use_case.execute("uid_abc", "gog_12345")

    assert result == []
    steam_metadata.get_app_details.assert_not_awaited()


@pytest.mark.asyncio
async def test_steam_app_id_extracted_from_game_id_prefix(
    use_case: GetGameDlcsUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
    game_reader: AsyncMock,
) -> None:
    repo.get_game.return_value = None  # not in cache
    base_game = SteamAppDetails(app_id=570, name="Dota 2", dlc_app_ids=[100])
    steam_metadata.get_app_details.side_effect = [base_game, _dlc_details(100, "DLC A")]
    game_reader.get_owned_game_ids.return_value = set()

    result = await use_case.execute("uid_abc", "steam_570")

    assert len(result) == 1
    assert result[0].name == "DLC A"


@pytest.mark.asyncio
async def test_no_dlcs_on_base_game_returns_empty(
    use_case: GetGameDlcsUseCase,
    repo: AsyncMock,
    steam_metadata: AsyncMock,
) -> None:
    repo.get_game.return_value = {"game_id": "steam_570", "steam_app_id": 570}
    steam_metadata.get_app_details.return_value = SteamAppDetails(
        app_id=570, name="Dota 2"
    )  # dlc_app_ids defaults to []

    result = await use_case.execute("uid_abc", "steam_570")

    assert result == []
