"""Tests for FirestoreSettingsRepository ITAD country methods."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.settings.infrastructure.repos.settings_repository import (
    FirestoreSettingsRepository,
)


def _make_doc(data: dict[str, Any] | None) -> MagicMock:
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data or {}
    return doc


@pytest.fixture
def mock_firestore() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo(mock_firestore: MagicMock) -> FirestoreSettingsRepository:
    with patch(
        "modules.settings.infrastructure.repos.settings_repository.get_firestore",
        return_value=mock_firestore,
    ):
        return FirestoreSettingsRepository()


# ---------------------------------------------------------------------------
# get_itad_country
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_itad_country_returns_code_when_exists(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc = _make_doc({"country_code": "ES"})
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_itad_country("uid-123")

    assert result == "ES"


@pytest.mark.asyncio
async def test_get_itad_country_returns_none_when_doc_missing(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc = _make_doc(None)
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_itad_country("uid-456")

    assert result is None


@pytest.mark.asyncio
async def test_get_itad_country_returns_none_when_field_missing(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc = _make_doc({})
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_itad_country("uid-789")

    assert result is None


# ---------------------------------------------------------------------------
# update_itad_country
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_itad_country_persists_code(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    set_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = set_mock

    await repo.update_itad_country("uid-abc", "MX")

    set_mock.assert_awaited_once_with({"country_code": "MX"})


@pytest.mark.asyncio
async def test_update_itad_country_writes_correct_path(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = AsyncMock()

    await repo.update_itad_country("uid-abc", "MX")

    # Verify the path chain: users/{uid}/settings/country
    mock_firestore.collection.assert_called_with("users")
    uid_doc = mock_firestore.collection.return_value.document.return_value
    settings_ref = uid_doc.collection.return_value
    settings_ref.document.assert_called_with("country")


@pytest.mark.asyncio
async def test_update_itad_country_overwrites_existing(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    set_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = set_mock

    await repo.update_itad_country("uid-abc", "DE")

    set_mock.assert_awaited_once_with({"country_code": "DE"})


# ---------------------------------------------------------------------------
# delete_all
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_all_does_not_remove_country(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    uid_doc = mock_firestore.collection.return_value.document.return_value
    settings_ref = uid_doc.collection.return_value

    doc_ref = repo._db.collection.return_value.document.return_value
    doc_ref.collection.return_value.document.return_value.delete = AsyncMock()
    # push token cleanup query returns no docs
    mock_firestore.collection.return_value.where.return_value.get = AsyncMock(return_value=[])

    await repo.delete_all("uid-123")

    # Should delete notifications subdoc, not country
    settings_ref.document.assert_called_with("notifications")


@pytest.mark.asyncio
async def test_delete_all_removes_push_tokens(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc_ref = repo._db.collection.return_value.document.return_value
    doc_ref.collection.return_value.document.return_value.delete = AsyncMock()

    token_doc = MagicMock()
    token_doc.reference.delete = AsyncMock()
    mock_firestore.collection.return_value.where.return_value.get = AsyncMock(
        return_value=[token_doc]
    )

    await repo.delete_all("uid-123")

    token_doc.reference.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# register_push_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_push_token_returns_token_id(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    mock_firestore.collection.return_value.document.return_value.set = AsyncMock()
    mock_firestore.collection.return_value.where.return_value.where.return_value.get = AsyncMock(
        return_value=[]
    )

    token_id = await repo.register_push_token("uid-abc", "ExponentPushToken[xxx]", "ios")

    assert token_id.startswith("ios_")


@pytest.mark.asyncio
async def test_register_push_token_deletes_stale_tokens(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    mock_firestore.collection.return_value.document.return_value.set = AsyncMock()

    stale = MagicMock()
    stale.reference.delete = AsyncMock()
    mock_firestore.collection.return_value.where.return_value.where.return_value.get = AsyncMock(
        return_value=[stale]
    )

    await repo.register_push_token("uid-abc", "ExponentPushToken[xxx]", "ios")
    # stale doc has a different id so it should be deleted
    stale.id = "old_token_id"

    # The cleanup runs — stale.reference.delete should have been called
    stale.reference.delete.assert_awaited()


# ---------------------------------------------------------------------------
# remove_push_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_push_token_deletes_when_uid_matches(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc = _make_doc({"uid": "uid-abc"})
    ref = mock_firestore.collection.return_value.document.return_value
    ref.get = AsyncMock(return_value=doc)
    ref.delete = AsyncMock()

    await repo.remove_push_token("uid-abc", "ios_token123")

    ref.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_push_token_does_nothing_when_uid_mismatch(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc = _make_doc({"uid": "other-uid"})
    ref = mock_firestore.collection.return_value.document.return_value
    ref.get = AsyncMock(return_value=doc)
    ref.delete = AsyncMock()

    await repo.remove_push_token("uid-abc", "ios_token123")

    ref.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_push_token_does_nothing_when_doc_missing(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc = _make_doc(None)
    ref = mock_firestore.collection.return_value.document.return_value
    ref.get = AsyncMock(return_value=doc)
    ref.delete = AsyncMock()

    await repo.remove_push_token("uid-abc", "ios_token123")

    ref.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# remove_all_push_tokens
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_all_push_tokens_deletes_all_docs(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    doc1, doc2 = MagicMock(), MagicMock()
    doc1.reference.delete = AsyncMock()
    doc2.reference.delete = AsyncMock()
    mock_firestore.collection.return_value.where.return_value.get = AsyncMock(
        return_value=[doc1, doc2]
    )

    await repo.remove_all_push_tokens("uid-abc")

    doc1.reference.delete.assert_awaited_once()
    doc2.reference.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_all_push_tokens_no_op_when_empty(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    mock_firestore.collection.return_value.where.return_value.get = AsyncMock(return_value=[])

    # Should not raise
    await repo.remove_all_push_tokens("uid-abc")


# ---------------------------------------------------------------------------
# Integration: full round-trip
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_round_trip_update_then_get(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    # Setup update path
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = AsyncMock()

    # Setup get path — return document with country_code
    doc = _make_doc({"country_code": "BR"})
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    await repo.update_itad_country("uid-rt", "BR")
    result = await repo.get_itad_country("uid-rt")

    assert result == "BR"
