"""Firestore implementation of the wishlist repository.

Stores wishlist items in the ``users/{uid}/wishlist/{game_id}``
subcollection. Also implements IWishlistReader for cross-module access.
"""

import asyncio
import logging
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

logger = logging.getLogger(__name__)

_COLLECTION = "users"
_SUBCOLLECTION = "wishlist"


class FirestoreWishlistRepository(BaseFirestoreRepository, IWishlistRepository, IWishlistReader):
    """IWishlistRepository + IWishlistReader backed by Firestore."""

    def __init__(self) -> None:
        super().__init__(client=get_firestore())

    async def get_items(self, uid: str) -> list[WishlistItem]:
        docs = await self.get_subcollection(_COLLECTION, uid, _SUBCOLLECTION)
        return [item for item in (_doc_to_wishlist_item(doc) for doc in docs) if item is not None]

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

    async def check_wishlist_ids(self, uid: str, game_ids: set[str]) -> set[str]:
        if not game_ids:
            return set()
        docs = await asyncio.gather(
            *[self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, gid) for gid in game_ids]
        )
        return {gid for gid, doc in zip(game_ids, docs, strict=True) if doc is not None}


def _doc_to_wishlist_item(doc: dict[str, Any]) -> WishlistItem | None:
    game_id = str(doc.get("game_id") or doc.get("gameId") or doc.get("__doc_id", ""))

    if not game_id:
        return None

    raw_platform = doc.get("platform", "")
    try:
        platform = Platform.from_raw(raw_platform)
    except ValueError:
        platform_prefix = game_id.split("_", 1)[0] if "_" in game_id else ""
        try:
            platform = Platform.from_raw(platform_prefix)
        except ValueError:
            # Legacy items written directly to Firestore before the API existed
            # have UUID game_ids with no platform field. Default to STEAM so they
            # remain visible; the user can re-add them properly if needed.
            if "-" in game_id and "_" not in game_id:
                platform = Platform.STEAM
                logger.warning(f"Defaulting platform to STEAM for legacy wishlist item {game_id}")
            else:
                logger.warning(f"Invalid platform for wishlist item {game_id}")
                return None

    raw_added_at = doc.get("added_at", doc.get("addedAt", ""))
    if hasattr(raw_added_at, "isoformat"):
        raw_added_at = raw_added_at.isoformat()

    title = doc.get("title", "")
    cover_url = doc.get("cover_url", doc.get("coverUrl"))

    return WishlistItem(
        game_id=game_id,
        title=title,
        platform=platform,
        cover_url=cover_url,
        added_at=raw_added_at,
    )
