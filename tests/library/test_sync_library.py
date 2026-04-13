"""Tests for SyncLibraryUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.library.application.sync_library_use_case import SyncLibraryUseCase
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


def _steam_library_game(app_id: int, title: str, playtime: int = 100) -> LibraryGame:
    return LibraryGame(
        game_id=f"steam_{app_id}",
        title=title,
        platform=Platform.STEAM,
        playtime_minutes=playtime,
        steam_app_id=app_id,
    )


def _gog_game(game_id: str, title: str) -> MagicMock:
    g = MagicMock()
    g.id = game_id
    g.title = title
    g.image_url = None
    return g


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def platform_reader() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def steam_library_source() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def epic_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def gog_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def psn_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(
    repo: AsyncMock,
    platform_reader: AsyncMock,
    steam_library_source: AsyncMock,
    epic_client: AsyncMock,
    gog_client: AsyncMock,
    psn_client: AsyncMock,
) -> SyncLibraryUseCase:
    return SyncLibraryUseCase(
        repo, platform_reader, steam_library_source, epic_client, gog_client, psn_client
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_steam_games_upserted(
    use_case: SyncLibraryUseCase,
    repo: AsyncMock,
    platform_reader: AsyncMock,
    steam_library_source: AsyncMock,
) -> None:
    platform_reader.get_linked_with_tokens.return_value = [
        (LinkedPlatform(platform=Platform.STEAM, username="76561198000000001"), {})
    ]
    steam_library_source.get_owned_games.return_value = [
        _steam_library_game(570, "Dota 2", playtime=500),
        _steam_library_game(440, "TF2", playtime=200),
    ]

    count = await use_case.execute("uid_abc")

    assert count == 2
    repo.upsert_games.assert_awaited_once()
    upserted = repo.upsert_games.call_args[0][1]
    assert upserted[0].game_id == "steam_570"
    assert upserted[1].game_id == "steam_440"


@pytest.mark.asyncio
async def test_sync_gog_games_upserted(
    use_case: SyncLibraryUseCase,
    repo: AsyncMock,
    platform_reader: AsyncMock,
    gog_client: AsyncMock,
) -> None:
    platform_reader.get_linked_with_tokens.return_value = [
        (LinkedPlatform(platform=Platform.GOG, username="gog_user"), {"access_token": "tok_123"})
    ]
    gog_client.get_user_games.return_value = [
        _gog_game("12345", "The Witcher 3"),
    ]

    count = await use_case.execute("uid_abc")

    assert count == 1
    upserted = repo.upsert_games.call_args[0][1]
    assert upserted[0].game_id == "gog_12345"
    assert upserted[0].platform == Platform.GOG


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_one_platform_fails_others_still_synced(
    use_case: SyncLibraryUseCase,
    repo: AsyncMock,
    platform_reader: AsyncMock,
    steam_library_source: AsyncMock,
    psn_client: AsyncMock,
) -> None:
    platform_reader.get_linked_with_tokens.return_value = [
        (LinkedPlatform(platform=Platform.STEAM, username="76561198000000001"), {}),
        (LinkedPlatform(platform=Platform.PSN, username="psn_user"), {"access_token": "tok"}),
    ]
    steam_library_source.get_owned_games.return_value = [_steam_library_game(570, "Dota 2")]
    psn_client.get_played_games.side_effect = Exception("PSN API timeout")

    count = await use_case.execute("uid_abc")

    assert count == 1
    repo.upsert_games.assert_awaited_once()


@pytest.mark.asyncio
async def test_platform_without_tokens_returns_empty(
    use_case: SyncLibraryUseCase,
    repo: AsyncMock,
    platform_reader: AsyncMock,
) -> None:
    platform_reader.get_linked_with_tokens.return_value = [
        (LinkedPlatform(platform=Platform.GOG, username="gog_user"), {})
    ]

    count = await use_case.execute("uid_abc")

    assert count == 0
    repo.upsert_games.assert_not_awaited()


# ---------------------------------------------------------------------------
# Platform filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_specific_platform_only(
    use_case: SyncLibraryUseCase,
    repo: AsyncMock,
    platform_reader: AsyncMock,
    steam_library_source: AsyncMock,
) -> None:
    platform_reader.get_linked_with_tokens.return_value = [
        (LinkedPlatform(platform=Platform.STEAM, username="76561198000000001"), {}),
        (LinkedPlatform(platform=Platform.GOG, username="gog_user"), {}),
    ]
    steam_library_source.get_owned_games.return_value = [_steam_library_game(570, "Dota 2")]

    count = await use_case.execute("uid_abc", platform=Platform.STEAM)

    assert count == 1
    steam_library_source.get_owned_games.assert_awaited_once()
