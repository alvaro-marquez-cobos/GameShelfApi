"""Tests for FirestoreGameRepository."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.games.infrastructure.repos.game_repository import FirestoreGameRepository


def _make_doc(data: dict[str, Any] | None) -> MagicMock:
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data or {}
    return doc


@pytest.fixture
def repo() -> FirestoreGameRepository:
    with patch(
        "modules.games.infrastructure.repos.game_repository.get_firestore",
        return_value=MagicMock(),
    ):
        return FirestoreGameRepository()


# ---------------------------------------------------------------------------
# get_game
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_game_returns_doc(repo: FirestoreGameRepository) -> None:
    repo._db.collection.return_value.document.return_value.get = AsyncMock(
        return_value=_make_doc({"game_id": "steam_570", "steam_app_id": 570})
    )

    result = await repo.get_game("steam_570")

    assert result == {"game_id": "steam_570", "steam_app_id": 570}


@pytest.mark.asyncio
async def test_get_game_returns_none_when_absent(repo: FirestoreGameRepository) -> None:
    repo._db.collection.return_value.document.return_value.get = AsyncMock(
        return_value=_make_doc(None)
    )

    result = await repo.get_game("steam_999")

    assert result is None


# ---------------------------------------------------------------------------
# update_steam_app_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_steam_app_id_calls_set_with_merge(repo: FirestoreGameRepository) -> None:
    set_mock = AsyncMock()
    repo._db.collection.return_value.document.return_value.set = set_mock

    await repo.update_steam_app_id("steam_570", 570)

    set_mock.assert_awaited_once_with({"game_id": "steam_570", "steam_app_id": 570}, merge=True)
