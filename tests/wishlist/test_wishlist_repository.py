"""Tests for FirestoreWishlistRepository."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.wishlist.domain.entities.wishlist_item import WishlistItem
from modules.wishlist.infrastructure.repos.wishlist_repository import (
    FirestoreWishlistRepository,
)
from shared.domain.enums.platform import Platform


def _make_doc(data: dict[str, Any] | None) -> MagicMock:
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data or {}
    doc.id = data.get("__doc_id", "") if data else ""
    return doc


@pytest.fixture
def repo() -> FirestoreWishlistRepository:
    with patch(
        "modules.wishlist.infrastructure.repos.wishlist_repository.get_firestore",
        return_value=MagicMock(),
    ):
        return FirestoreWishlistRepository()


# ---------------------------------------------------------------------------
# get_items
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_items_returns_all_wishlist_games(repo: FirestoreWishlistRepository) -> None:
    docs = [
        _make_doc(
            {
                "game_id": "steam_1145360",
                "title": "Hades",
                "platform": "steam",
                "added_at": "2026-01-01",
            }
        ),
        _make_doc(
            {
                "game_id": "epic_celeste",
                "title": "Celeste",
                "platform": "epic",
                "added_at": "2026-01-02",
            }
        ),
    ]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_items("uid_abc")

    assert len(result) == 2
    assert result[0].game_id == "steam_1145360"
    assert result[0].title == "Hades"
    assert result[1].platform == Platform.EPIC


@pytest.mark.asyncio
async def test_get_items_returns_empty_list_when_wishlist_empty(
    repo: FirestoreWishlistRepository,
) -> None:
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=[])

    result = await repo.get_items("uid_abc")

    assert result == []


@pytest.mark.asyncio
async def test_get_items_reads_legacy_frontend_shape(repo: FirestoreWishlistRepository) -> None:
    docs = [
        _make_doc(
            {
                "gameId": "steam_570",
                "title": "Dota 2",
                "coverUrl": "https://example.com/dota2.png",
                "addedAt": "2026-01-01T00:00:00",
                "__doc_id": "steam_570",
            }
        )
    ]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_items("uid_abc")

    assert len(result) == 1
    assert result[0].game_id == "steam_570"
    assert result[0].platform == Platform.STEAM


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_writes_wishlist_document(repo: FirestoreWishlistRepository) -> None:
    set_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = set_mock

    item = WishlistItem(
        game_id="steam_1145360",
        title="Hades",
        platform=Platform.STEAM,
        cover_url="https://example.com/hades.jpg",
        added_at="2026-01-01T00:00:00",
    )
    await repo.add("uid_abc", item)

    set_mock.assert_awaited_once()
    written = set_mock.call_args[0][0]
    assert written["game_id"] == "steam_1145360"
    assert written["title"] == "Hades"
    assert written["platform"] == Platform.STEAM


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_deletes_wishlist_document(repo: FirestoreWishlistRepository) -> None:
    delete_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete
    ) = delete_mock

    await repo.remove("uid_abc", "steam_1145360")

    delete_mock.assert_awaited_once()


# ---------------------------------------------------------------------------
# is_in_wishlist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_in_wishlist_returns_true_when_present(
    repo: FirestoreWishlistRepository,
) -> None:
    doc = _make_doc({"game_id": "steam_1145360"})
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.is_in_wishlist("uid_abc", "steam_1145360")

    assert result is True


@pytest.mark.asyncio
async def test_is_in_wishlist_returns_false_when_absent(
    repo: FirestoreWishlistRepository,
) -> None:
    doc = _make_doc(None)
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.is_in_wishlist("uid_abc", "steam_9999")

    assert result is False


# ---------------------------------------------------------------------------
# get_wishlist_ids (IWishlistReader)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_wishlist_ids_returns_set_of_game_ids(
    repo: FirestoreWishlistRepository,
) -> None:
    docs = [
        _make_doc({"game_id": "steam_1145360"}),
        _make_doc({"game_id": "epic_celeste"}),
        _make_doc({"game_id": "gog_witcher3"}),
    ]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_wishlist_ids("uid_abc")

    assert result == {"steam_1145360", "epic_celeste", "gog_witcher3"}


@pytest.mark.asyncio
async def test_get_wishlist_ids_returns_empty_set_when_empty(
    repo: FirestoreWishlistRepository,
) -> None:
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=[])

    result = await repo.get_wishlist_ids("uid_abc")

    assert result == set()
