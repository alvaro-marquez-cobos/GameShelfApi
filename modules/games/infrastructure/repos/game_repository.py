"""Firestore implementation of the game metadata repository.

Stores enriched game documents in the top-level ``games/{game_id}`` collection.
"""

from typing import Any

from modules.games.domain.interfaces.repositories.i_game_repository import IGameRepository
from shared.infrastructure.database.firestore import get_firestore
from shared.infrastructure.persistence.base_repository import BaseFirestoreRepository

_COLLECTION = "games"


class FirestoreGameRepository(BaseFirestoreRepository, IGameRepository):
    """IGameRepository backed by Firestore."""

    def __init__(self) -> None:
        super().__init__(client=get_firestore())

    async def get_game(self, game_id: str) -> dict[str, Any] | None:
        return await self.get_doc(_COLLECTION, game_id)

    async def update_steam_app_id(self, game_id: str, steam_app_id: int) -> None:
        # Use Firestore set with merge=True so the doc is created if absent.
        await (
            self._db.collection(_COLLECTION)
            .document(game_id)
            .set({"game_id": game_id, "steam_app_id": steam_app_id}, merge=True)
        )
