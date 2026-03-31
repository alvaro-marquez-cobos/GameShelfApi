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


def _doc_to_library_game(doc: dict[str, Any]) -> LibraryGame:
    return LibraryGame(
        game_id=doc["game_id"],
        title=doc.get("title", ""),
        platform=Platform(doc["platform"]),
        cover_url=doc.get("cover_url"),
        playtime_minutes=doc.get("playtime_minutes", 0),
        last_played=doc.get("last_played"),
        steam_app_id=doc.get("steam_app_id"),
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
