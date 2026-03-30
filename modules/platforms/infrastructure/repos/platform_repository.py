"""Firestore implementation of the platform repository.

Stores linked platform accounts in the ``users/{uid}/platforms/{platform}``
subcollection. Also implements IPlatformReader for cross-module access.
"""

from datetime import UTC, datetime
from typing import Any

from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.i_platform_reader import IPlatformReader
from shared.infrastructure.database.firestore import get_firestore
from shared.infrastructure.persistence.base_repository import BaseFirestoreRepository

_COLLECTION = "users"
_SUBCOLLECTION = "platforms"


class FirestorePlatformRepository(BaseFirestoreRepository, IPlatformRepository, IPlatformReader):
    """IPlatformRepository + IPlatformReader backed by Firestore."""

    def __init__(self) -> None:
        super().__init__(client=get_firestore())

    async def get_linked(self, uid: str) -> list[LinkedPlatform]:
        docs = await self.get_subcollection(_COLLECTION, uid, _SUBCOLLECTION)
        return [_doc_to_linked_platform(doc) for doc in docs]

    async def link(self, uid: str, platform_data: LinkedPlatform) -> None:
        data: dict[str, Any] = {
            "platform": platform_data.platform,
            "username": platform_data.username,
            "avatar_url": platform_data.avatar_url,
            "linked_at": platform_data.linked_at or datetime.now(UTC).isoformat(),
        }
        await self.set_subdoc(_COLLECTION, uid, _SUBCOLLECTION, platform_data.platform, data)

    async def unlink(self, uid: str, platform: Platform) -> None:
        await self.delete_subdoc(_COLLECTION, uid, _SUBCOLLECTION, platform)

    async def get_tokens(self, uid: str, platform: Platform) -> dict[str, Any] | None:
        doc = await self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, platform)
        if doc is None:
            return None
        return {
            k: v
            for k, v in doc.items()
            if k in ("access_token", "refresh_token", "token_expires_at")
        }

    async def store_tokens(self, uid: str, platform: Platform, tokens: dict[str, Any]) -> None:
        await self.update_subdoc(_COLLECTION, uid, _SUBCOLLECTION, platform, tokens)

    # IPlatformReader
    async def get_linked_platforms(self, uid: str) -> list[LinkedPlatform]:
        return await self.get_linked(uid)


def _doc_to_linked_platform(doc: dict[str, Any]) -> LinkedPlatform:
    return LinkedPlatform(
        platform=Platform(doc["platform"]),
        username=doc.get("username", ""),
        avatar_url=doc.get("avatar_url"),
        linked_at=doc.get("linked_at", ""),
    )
