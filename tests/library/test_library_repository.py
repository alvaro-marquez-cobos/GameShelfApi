"""Tests for FirestoreLibraryRepository."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.library.domain.entities.library_game import LibraryGame
from modules.library.infrastructure.repos.library_repository import (
    FirestoreLibraryRepository,
)
from shared.domain.enums.platform import Platform


def _make_doc(data: dict[str, Any] | None) -> MagicMock:
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data or {}
    return doc


@pytest.fixture
def repo() -> FirestoreLibraryRepository:
    with patch(
        "modules.library.infrastructure.repos.library_repository.get_firestore",
        return_value=MagicMock(),
    ):
        return FirestoreLibraryRepository()


def _steam_game_doc(game_id: str = "steam_570", title: str = "Dota 2") -> dict[str, Any]:
    return {
        "game_id": game_id,
        "title": title,
        "platform": "steam",
        "cover_url": None,
        "playtime_minutes": 300,
        "last_played": "2026-01-01T00:00:00+00:00",
        "steam_app_id": 570,
        "extra": {},
    }


# ---------------------------------------------------------------------------
# get_games
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_games_returns_all_library_entries(repo: FirestoreLibraryRepository) -> None:
    docs = [_make_doc(_steam_game_doc()), _make_doc(_steam_game_doc("steam_440", "TF2"))]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_games("uid_abc")

    assert len(result) == 2
    assert result[0].game_id == "steam_570"
    assert result[1].title == "TF2"


@pytest.mark.asyncio
async def test_get_games_returns_empty_when_library_empty(
    repo: FirestoreLibraryRepository,
) -> None:
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=[])

    result = await repo.get_games("uid_abc")

    assert result == []


# ---------------------------------------------------------------------------
# get_game
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_game_returns_game_when_exists(repo: FirestoreLibraryRepository) -> None:
    doc = _make_doc(_steam_game_doc())
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_game("uid_abc", "steam_570")

    assert result is not None
    assert result.game_id == "steam_570"
    assert result.platform == Platform.STEAM


@pytest.mark.asyncio
async def test_get_game_returns_none_when_missing(repo: FirestoreLibraryRepository) -> None:
    doc = _make_doc(None)
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_game("uid_abc", "steam_9999")

    assert result is None


# ---------------------------------------------------------------------------
# upsert_games
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_games_writes_all_documents(repo: FirestoreLibraryRepository) -> None:
    set_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = set_mock

    games = [
        LibraryGame(game_id="steam_570", title="Dota 2", platform=Platform.STEAM),
        LibraryGame(game_id="steam_440", title="TF2", platform=Platform.STEAM),
    ]
    await repo.upsert_games("uid_abc", games)

    assert set_mock.await_count == 2


# ---------------------------------------------------------------------------
# get_owned_game_ids (IGameReader)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_owned_game_ids_returns_set(repo: FirestoreLibraryRepository) -> None:
    docs = [
        _make_doc({"game_id": "steam_570"}),
        _make_doc({"game_id": "epic_fn_fortnite"}),
        _make_doc({"game_id": "gog_123"}),
    ]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_owned_game_ids("uid_abc")

    assert result == {"steam_570", "epic_fn_fortnite", "gog_123"}


@pytest.mark.asyncio
async def test_get_owned_game_ids_returns_empty_set_when_no_games(
    repo: FirestoreLibraryRepository,
) -> None:
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=[])

    result = await repo.get_owned_game_ids("uid_abc")

    assert result == set()
