"""Firestore implementation of the settings repository.

Stores user settings in the ``users/{uid}/settings`` document.
"""

from typing import Any

from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from shared.infrastructure.database.firestore import get_firestore
from shared.infrastructure.persistence.base_repository import BaseFirestoreRepository

_COLLECTION = "users"
_SUBCOLLECTION = "settings"


class FirestoreSettingsRepository(BaseFirestoreRepository, ISettingsRepository):
    """ISettingsRepository backed by Firestore."""

    def __init__(self) -> None:
        super().__init__(client=get_firestore())

    async def get_notification_prefs(self, uid: str) -> dict[str, Any] | None:
        doc = await self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, "notifications")
        if doc is None:
            return None
        return doc.get("preferences")

    async def update_notification_prefs(self, uid: str, prefs: dict[str, Any]) -> None:
        await self.set_subdoc(
            _COLLECTION, uid, _SUBCOLLECTION, "notifications", {"preferences": prefs}
        )

    async def delete_all(self, uid: str) -> None:
        await self.delete_subdoc(_COLLECTION, uid, _SUBCOLLECTION, "notifications")
