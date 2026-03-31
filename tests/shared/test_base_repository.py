"""Tests for the BaseFirestoreRepository CRUD helpers."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from shared.infrastructure.persistence.base_repository import BaseFirestoreRepository


def _make_doc(data: dict[str, Any] | None) -> MagicMock:
    """Build a mock Firestore DocumentSnapshot."""
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data or {}
    doc.id = data.get("__doc_id", "") if data else ""
    return doc


@pytest.fixture
def db() -> MagicMock:
    """Return a mock Firestore AsyncClient."""
    return MagicMock()


@pytest.fixture
def repo(db: MagicMock) -> BaseFirestoreRepository:
    return BaseFirestoreRepository(client=db)


# ---------------------------------------------------------------------------
# get_doc
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_doc_returns_data_when_exists(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    doc = _make_doc({"title": "Hades"})
    db.collection.return_value.document.return_value.get = AsyncMock(return_value=doc)

    result = await repo.get_doc("games", "steam_1145360")

    assert result == {"title": "Hades"}


@pytest.mark.asyncio
async def test_get_doc_returns_none_when_missing(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    doc = _make_doc(None)
    db.collection.return_value.document.return_value.get = AsyncMock(return_value=doc)

    result = await repo.get_doc("games", "steam_9999")

    assert result is None


# ---------------------------------------------------------------------------
# set_doc
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_doc_calls_firestore_set(repo: BaseFirestoreRepository, db: MagicMock) -> None:
    set_mock = AsyncMock()
    db.collection.return_value.document.return_value.set = set_mock

    await repo.set_doc("games", "steam_1145360", {"title": "Hades"})

    set_mock.assert_awaited_once_with({"title": "Hades"})


# ---------------------------------------------------------------------------
# update_doc
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_doc_calls_firestore_update(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    update_mock = AsyncMock()
    db.collection.return_value.document.return_value.update = update_mock

    await repo.update_doc("games", "steam_1145360", {"steam_app_id": 1145360})

    update_mock.assert_awaited_once_with({"steam_app_id": 1145360})


# ---------------------------------------------------------------------------
# delete_doc
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_doc_calls_firestore_delete(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    delete_mock = AsyncMock()
    db.collection.return_value.document.return_value.delete = delete_mock

    await repo.delete_doc("games", "steam_1145360")

    delete_mock.assert_awaited_once()


# ---------------------------------------------------------------------------
# query_collection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_collection_without_filters(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    docs = [_make_doc({"title": "Hades"}), _make_doc({"title": "Celeste"})]
    db.collection.return_value.get = AsyncMock(return_value=docs)

    result = await repo.query_collection("games")

    assert result == [{"title": "Hades"}, {"title": "Celeste"}]


@pytest.mark.asyncio
async def test_query_collection_with_filters(repo: BaseFirestoreRepository, db: MagicMock) -> None:
    filtered_ref = MagicMock()
    filtered_ref.get = AsyncMock(return_value=[_make_doc({"platform": "steam"})])
    db.collection.return_value.where.return_value = filtered_ref

    result = await repo.query_collection("games", filters=[("platform", "==", "steam")])

    assert result == [{"platform": "steam"}]
    db.collection.return_value.where.assert_called_once_with("platform", "==", "steam")


# ---------------------------------------------------------------------------
# Subcollection helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_subcollection_returns_all_docs(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    docs = [_make_doc({"game_id": "steam_570"}), _make_doc({"game_id": "epic_fn"})]
    (db.collection.return_value.document.return_value.collection.return_value.get) = AsyncMock(
        return_value=docs
    )

    result = await repo.get_subcollection("users", "uid_abc", "library")

    assert len(result) == 2
    assert result[0]["game_id"] == "steam_570"


@pytest.mark.asyncio
async def test_get_subdoc_returns_data_when_exists(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    doc = _make_doc({"game_id": "steam_570", "playtime_minutes": 120})
    (
        db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_subdoc("users", "uid_abc", "library", "steam_570")

    assert result is not None
    assert result["game_id"] == "steam_570"
    assert result["playtime_minutes"] == 120
    assert result["__doc_id"] == ""


@pytest.mark.asyncio
async def test_get_subdoc_returns_none_when_missing(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    doc = _make_doc(None)
    (
        db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_subdoc("users", "uid_abc", "library", "steam_9999")

    assert result is None


@pytest.mark.asyncio
async def test_set_subdoc_calls_firestore_set(repo: BaseFirestoreRepository, db: MagicMock) -> None:
    set_mock = AsyncMock()
    (
        db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = set_mock

    await repo.set_subdoc("users", "uid_abc", "library", "steam_570", {"title": "Dota 2"})

    set_mock.assert_awaited_once_with({"title": "Dota 2"})


@pytest.mark.asyncio
async def test_delete_subdoc_calls_firestore_delete(
    repo: BaseFirestoreRepository, db: MagicMock
) -> None:
    delete_mock = AsyncMock()
    (
        db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete
    ) = delete_mock

    await repo.delete_subdoc("users", "uid_abc", "library", "steam_570")

    delete_mock.assert_awaited_once()
