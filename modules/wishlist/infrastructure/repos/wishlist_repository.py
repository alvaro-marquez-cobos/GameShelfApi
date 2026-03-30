"""Firestore implementation of the wishlist repository.

Stores wishlist items in the ``users/{uid}/wishlist/{game_id}``
subcollection. Also implements IWishlistReader for cross-module access.
"""

from datetime import UTC, datetime
from typing import Any

from modules.wishlist.domain.entities.wishlist_item import WishlistItem
from modules.wishlist.domain.interfaces.repositories.i_wishlist_repository import (
    IWishlistRepository,
)
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.i_wishlist_reader import IWishlistReader
from shared.infrastructure.database.firestore import get_firestore
from shared.infrastructure.persistence.base_repository import BaseFirestoreRepository

_COLLECTION = "users"
_SUBCOLLECTION = "wishlist"


class FirestoreWishlistRepository(BaseFirestoreRepository, IWishlistRepository, IWishlistReader):
    """IWishlistRepository + IWishlistReader backed by Firestore."""

    def __init__(self) -> None:
        super().__init__(client=get_firestore())

    async def get_items(self, uid: str) -> list[WishlistItem]:
        docs = await self.get_subcollection(_COLLECTION, uid, _SUBCOLLECTION)
        return [_doc_to_wishlist_item(doc) for doc in docs]

    async def add(self, uid: str, item: WishlistItem) -> None:
        data: dict[str, Any] = {
            "game_id": item.game_id,
            "title": item.title,
            "platform": item.platform,
            "cover_url": item.cover_url,
            "added_at": item.added_at or datetime.now(UTC).isoformat(),
        }
        await self.set_subdoc(_COLLECTION, uid, _SUBCOLLECTION, item.game_id, data)

    async def remove(self, uid: str, game_id: str) -> None:
        await self.delete_subdoc(_COLLECTION, uid, _SUBCOLLECTION, game_id)

    async def is_in_wishlist(self, uid: str, game_id: str) -> bool:
        doc = await self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, game_id)
        return doc is not None

    # IWishlistReader
    async def get_wishlist_ids(self, uid: str) -> set[str]:
        docs = await self.get_subcollection(_COLLECTION, uid, _SUBCOLLECTION)
        return {doc["game_id"] for doc in docs if "game_id" in doc}


def _doc_to_wishlist_item(doc: dict[str, Any]) -> WishlistItem:
    return WishlistItem(
        game_id=doc["game_id"],
        title=doc.get("title", ""),
        platform=Platform(doc["platform"]),
        cover_url=doc.get("cover_url"),
        added_at=doc.get("added_at", ""),
    )
