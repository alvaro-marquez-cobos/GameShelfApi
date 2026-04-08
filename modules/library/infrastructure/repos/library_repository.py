"""Firestore implementation of the library repository.

Stores game entries in the ``users/{uid}/library/{game_id}`` subcollection.
Also implements IGameReader for cross-module access.
"""

import asyncio
from typing import Any

from modules.library.domain.interfaces.repositories.i_library_repository import (
    ILibraryRepository,
)
from shared.domain.entities.library_game import LibraryGame
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.i_game_reader import IGameReader
from shared.infrastructure.database.firestore import get_firestore
from shared.infrastructure.persistence.base_repository import BaseFirestoreRepository

_COLLECTION = "users"
_SUBCOLLECTION = "library"


class FirestoreLibraryRepository(BaseFirestoreRepository, ILibraryRepository, IGameReader):
    """ILibraryRepository + IGameReader backed by Firestore."""

    def __init__(self) -> None:
        super().__init__(client=get_firestore())

    async def get_games(self, uid: str) -> list[LibraryGame]:
        docs = await self.get_subcollection(_COLLECTION, uid, _SUBCOLLECTION)
        return [_doc_to_library_game(doc) for doc in docs]

    async def get_most_played(self, uid: str, limit: int) -> list[LibraryGame]:
        docs = await self.get_subcollection_ordered_limited(
            _COLLECTION,
            uid,
            _SUBCOLLECTION,
            order_by="playtime_minutes",
            direction="DESCENDING",
            limit=limit,
        )
        return [_doc_to_library_game(doc) for doc in docs]

    async def get_game(self, uid: str, game_id: str) -> LibraryGame | None:
        doc = await self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, game_id)
        if doc is None:
            return None
        return _doc_to_library_game(doc)

    async def upsert_games(self, uid: str, games: list[LibraryGame]) -> None:
        tasks = [
            self.set_subdoc(_COLLECTION, uid, _SUBCOLLECTION, g.game_id, _library_game_to_doc(g))
            for g in games
        ]
        await asyncio.gather(*tasks)

    # IGameReader
    async def get_owned_game_ids(self, uid: str) -> set[str]:
        docs = await self.get_subcollection(_COLLECTION, uid, _SUBCOLLECTION)
        return {doc["game_id"] for doc in docs if "game_id" in doc}

    async def check_owned_game_ids(self, uid: str, game_ids: set[str]) -> set[str]:
        if not game_ids:
            return set()
        docs = await asyncio.gather(
            *[self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, gid) for gid in game_ids]
        )
        return {gid for gid, doc in zip(game_ids, docs, strict=True) if doc is not None}


def _doc_to_library_game(doc: dict[str, Any]) -> LibraryGame:
    raw_platform = doc.get("platform", "")
    game_id = str(doc.get("game_id") or doc.get("gameId") or doc.get("__doc_id", ""))
    try:
        platform = Platform.from_raw(raw_platform)
    except ValueError:
        platform_prefix = game_id.split("_", 1)[0] if "_" in game_id else ""
        platform = Platform.from_raw(platform_prefix)

    raw_last_played = doc.get("last_played", doc.get("lastPlayed"))
    if raw_last_played is not None and not isinstance(raw_last_played, str):
        to_iso = getattr(raw_last_played, "isoformat", None)
        if callable(to_iso):
            raw_last_played = str(to_iso())

    return LibraryGame(
        game_id=game_id,
        title=doc.get("title", ""),
        platform=platform,
        cover_url=doc.get("cover_url", doc.get("coverUrl")),
        playtime_minutes=doc.get("playtime_minutes", doc.get("playtime", 0)),
        last_played=raw_last_played,
        steam_app_id=doc.get("steam_app_id", doc.get("steamAppId")),
        extra=doc.get("extra", {}),
    )


def _library_game_to_doc(game: LibraryGame) -> dict[str, Any]:
    return {
        "game_id": game.game_id,
        "title": game.title,
        "platform": game.platform,
        "cover_url": game.cover_url,
        "playtime_minutes": game.playtime_minutes,
        "last_played": game.last_played,
        "steam_app_id": game.steam_app_id,
        "extra": game.extra,
    }
