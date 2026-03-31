"""Tests for FirestorePlatformRepository."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.platforms.infrastructure.repos.platform_repository import (
    FirestorePlatformRepository,
)
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


def _make_doc(data: dict[str, Any] | None) -> MagicMock:
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data or {}
    doc.id = data.get("__doc_id", "") if data else ""
    return doc


@pytest.fixture
def repo() -> FirestorePlatformRepository:
    with patch(
        "modules.platforms.infrastructure.repos.platform_repository.get_firestore",
        return_value=MagicMock(),
    ):
        return FirestorePlatformRepository()


# ---------------------------------------------------------------------------
# get_linked / get_linked_platforms
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_linked_returns_all_platforms(repo: FirestorePlatformRepository) -> None:
    docs = [
        _make_doc({"platform": "steam", "username": "gamer1", "linked_at": "2026-01-01T00:00:00"}),
        _make_doc({"platform": "gog", "username": "gamer1", "linked_at": "2026-01-02T00:00:00"}),
    ]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_linked("uid_abc")

    assert len(result) == 2
    assert result[0].platform == Platform.STEAM
    assert result[1].platform == Platform.GOG


@pytest.mark.asyncio
async def test_get_linked_returns_empty_when_no_platforms(
    repo: FirestorePlatformRepository,
) -> None:
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=[])

    result = await repo.get_linked("uid_abc")

    assert result == []


@pytest.mark.asyncio
async def test_get_linked_platforms_delegates_to_get_linked(
    repo: FirestorePlatformRepository,
) -> None:
    docs = [_make_doc({"platform": "psn", "username": "gamer_ps", "linked_at": "2026-01-01"})]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_linked_platforms("uid_abc")

    assert len(result) == 1
    assert result[0].platform == Platform.PSN


@pytest.mark.asyncio
async def test_get_linked_reads_legacy_frontend_shape(
    repo: FirestorePlatformRepository,
) -> None:
    docs = [
        _make_doc(
            {
                "externalUserId": "epic_account_7",
                "linkedAt": "2026-01-03T00:00:00",
                "__doc_id": "epic_games",
            }
        )
    ]
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.get
    ) = AsyncMock(return_value=docs)

    result = await repo.get_linked("uid_abc")

    assert len(result) == 1
    assert result[0].platform == Platform.EPIC
    assert result[0].username == "epic_account_7"
    assert result[0].linked_at == "2026-01-03T00:00:00"


# ---------------------------------------------------------------------------
# link
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_link_writes_platform_document(repo: FirestorePlatformRepository) -> None:
    set_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    ) = set_mock

    platform_data = LinkedPlatform(
        platform=Platform.STEAM,
        username="steamuser",
        avatar_url="https://example.com/avatar.jpg",
        linked_at="2026-01-01T00:00:00",
    )
    await repo.link("uid_abc", platform_data)

    set_mock.assert_awaited_once()
    written = set_mock.call_args[0][0]
    assert written["platform"] == Platform.STEAM
    assert written["username"] == "steamuser"


# ---------------------------------------------------------------------------
# unlink
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unlink_deletes_platform_document(repo: FirestorePlatformRepository) -> None:
    delete_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete
    ) = delete_mock

    await repo.unlink("uid_abc", Platform.STEAM)

    delete_mock.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_tokens / store_tokens
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_tokens_returns_token_fields_only(repo: FirestorePlatformRepository) -> None:
    doc = _make_doc(
        {
            "platform": "steam",
            "username": "gamer1",
            "access_token": "tok_abc",
            "refresh_token": "ref_xyz",
            "token_expires_at": "2026-12-31T00:00:00",
            "account_id": "acc_1",
            "expires_at": "2027-01-01T00:00:00",
        }
    )
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_tokens("uid_abc", Platform.STEAM)

    assert result == {
        "access_token": "tok_abc",
        "refresh_token": "ref_xyz",
        "token_expires_at": "2026-12-31T00:00:00",
        "account_id": "acc_1",
        "expires_at": "2027-01-01T00:00:00",
    }


@pytest.mark.asyncio
async def test_get_tokens_returns_none_when_platform_not_linked(
    repo: FirestorePlatformRepository,
) -> None:
    doc = _make_doc(None)
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.get
    ) = AsyncMock(return_value=doc)

    result = await repo.get_tokens("uid_abc", Platform.EPIC)

    assert result is None


@pytest.mark.asyncio
async def test_store_tokens_updates_document(repo: FirestorePlatformRepository) -> None:
    update_mock = AsyncMock()
    (
        repo._db.collection.return_value.document.return_value.collection.return_value.document.return_value.update
    ) = update_mock

    tokens = {"access_token": "new_tok", "refresh_token": "new_ref"}
    await repo.store_tokens("uid_abc", Platform.GOG, tokens)

    update_mock.assert_awaited_once_with(tokens)
