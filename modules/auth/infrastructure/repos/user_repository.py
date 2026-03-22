"""Firestore implementation of the user repository.

Stores user profiles in the ``users`` collection, keyed by Firebase UID.
Handles created_at/updated_at timestamps automatically on upsert.
"""

from datetime import UTC, datetime
from typing import Any

from shared.domain.entities.user import AuthenticatedUser
from shared.domain.interfaces.user_repository import IUserRepository
from shared.infrastructure.database.firestore import get_firestore

_COLLECTION = "users"


class FirestoreUserRepository(IUserRepository):
    """IUserRepository backed by Google Cloud Firestore."""
    async def find_by_uid(self, uid: str) -> dict[str, Any] | None:
        db = get_firestore()
        doc_ref = db.collection(_COLLECTION).document(uid)
        doc = await doc_ref.get()
        if not doc.exists:
            return None
        data: dict[str, Any] = doc.to_dict() or {}
        return data

    async def upsert(self, user: AuthenticatedUser) -> dict[str, Any]:
        db = get_firestore()
        doc_ref = db.collection(_COLLECTION).document(user.uid)
        now = datetime.now(UTC).isoformat()

        existing = await doc_ref.get()
        created_at = now
        if existing.exists:
            existing_data: dict[str, Any] = existing.to_dict() or {}
            created_at = existing_data.get("created_at", now)

        data: dict[str, Any] = {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "is_guest": user.is_guest,
            "provider": user.provider,
            "updated_at": now,
            "created_at": created_at,
        }
        await doc_ref.set(data)
        return data

    async def delete(self, uid: str) -> None:
        db = get_firestore()
        doc_ref = db.collection(_COLLECTION).document(uid)
        await doc_ref.delete()
