"""Tests for FirestoreSettingsRepository ITAD country methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.settings.infrastructure.repos.settings_repository import (
    FirestoreSettingsRepository,
)


def _make_doc(data: dict | None) -> MagicMock:
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
# delete_all — should not affect country (only notifications)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_all_does_not_remove_country(
    repo: FirestoreSettingsRepository,
    mock_firestore: MagicMock,
) -> None:
    uid_doc = mock_firestore.collection.return_value.document.return_value
    settings_ref = uid_doc.collection.return_value

    # Set up delete mock before calling delete_all
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete
    ) = AsyncMock()

    await repo.delete_all("uid-123")

    # Should only delete notifications subdoc, not country
    settings_ref.document.assert_called_with("notifications")


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
