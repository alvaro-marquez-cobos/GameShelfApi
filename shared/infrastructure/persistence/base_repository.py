"""Base Firestore repository with common async CRUD helpers.

All module-specific repositories extend this class to avoid duplicating
Firestore boilerplate.
"""

from typing import Any

from google.cloud import firestore_v1


class BaseFirestoreRepository:
    """Provides low-level async Firestore helpers for subclasses.

    Args:
        client: An initialized Firestore async client.
    """

    def __init__(self, client: firestore_v1.AsyncClient) -> None:
        self._db: Any = client

    # ------------------------------------------------------------------
    # Top-level collection helpers
    # ------------------------------------------------------------------

    async def get_doc(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        """Return a document by collection and ID, or None if absent."""
        doc = await self._db.collection(collection).document(doc_id).get()
        if not doc.exists:
            return None
        return doc.to_dict() or {}

    async def set_doc(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        """Create or overwrite a document."""
        await self._db.collection(collection).document(doc_id).set(data)

    async def update_doc(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        """Merge-update specific fields on an existing document."""
        await self._db.collection(collection).document(doc_id).update(data)

    async def delete_doc(self, collection: str, doc_id: str) -> None:
        """Delete a document. No-op if it does not exist."""
        await self._db.collection(collection).document(doc_id).delete()

    async def query_collection(
        self,
        collection: str,
        filters: list[tuple[str, str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Return all documents in a collection, optionally filtered.

        Args:
            collection: Firestore collection path.
            filters: List of ``(field, operator, value)`` triples applied
                as ``where`` clauses (e.g. ``[("platform", "==", "steam")]``).
        """
        ref: Any = self._db.collection(collection)
        if filters:
            for field, op, value in filters:
                ref = ref.where(field, op, value)
        docs = await ref.get()
        return [doc.to_dict() or {} for doc in docs]

    # ------------------------------------------------------------------
    # Subcollection helpers (users/{uid}/{subcollection}/{subdoc_id})
    # ------------------------------------------------------------------

    async def get_subcollection(
        self, collection: str, doc_id: str, subcollection: str
    ) -> list[dict[str, Any]]:
        """Return all documents in a subcollection."""
        docs = (
            await self._db.collection(collection).document(doc_id).collection(subcollection).get()
        )
        result: list[dict[str, Any]] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["__doc_id"] = doc.id
            result.append(data)
        return result

    async def get_subcollection_ordered_limited(
        self,
        collection: str,
        doc_id: str,
        subcollection: str,
        order_by: str,
        direction: str = "DESCENDING",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return up to ``limit`` documents from a subcollection, ordered by a field.

        Uses a native Firestore query so only ``limit`` documents are read,
        instead of fetching the entire subcollection.
        """
        ref = (
            self._db.collection(collection)
            .document(doc_id)
            .collection(subcollection)
            .order_by(order_by, direction=direction)
            .limit(limit)
        )
        docs = await ref.get()
        result: list[dict[str, Any]] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["__doc_id"] = doc.id
            result.append(data)
        return result

    async def get_subdoc(
        self,
        collection: str,
        doc_id: str,
        subcollection: str,
        subdoc_id: str,
    ) -> dict[str, Any] | None:
        """Return a single subcollection document, or None if absent."""
        ref = (
            self._db.collection(collection)
            .document(doc_id)
            .collection(subcollection)
            .document(subdoc_id)
        )
        doc = await ref.get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data["__doc_id"] = doc.id
        return data

    async def set_subdoc(
        self,
        collection: str,
        doc_id: str,
        subcollection: str,
        subdoc_id: str,
        data: dict[str, Any],
    ) -> None:
        """Create or overwrite a subcollection document."""
        ref = (
            self._db.collection(collection)
            .document(doc_id)
            .collection(subcollection)
            .document(subdoc_id)
        )
        await ref.set(data)

    async def update_subdoc(
        self,
        collection: str,
        doc_id: str,
        subcollection: str,
        subdoc_id: str,
        data: dict[str, Any],
    ) -> None:
        """Merge-update specific fields on a subcollection document."""
        ref = (
            self._db.collection(collection)
            .document(doc_id)
            .collection(subcollection)
            .document(subdoc_id)
        )
        await ref.update(data)

    async def delete_subdoc(
        self,
        collection: str,
        doc_id: str,
        subcollection: str,
        subdoc_id: str,
    ) -> None:
        """Delete a subcollection document. No-op if it does not exist."""
        ref = (
            self._db.collection(collection)
            .document(doc_id)
            .collection(subcollection)
            .document(subdoc_id)
        )
        await ref.delete()
