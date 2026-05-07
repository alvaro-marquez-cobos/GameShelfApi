"""Firestore implementation of the settings repository.

Stores user settings in the ``users/{uid}/settings`` subcollection and push
notification tokens in a top-level ``pushTokens`` collection for efficient
bulk querying by the DealChecker service.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from shared.infrastructure.database.firestore import get_firestore
from shared.infrastructure.persistence.base_repository import BaseFirestoreRepository

logger = logging.getLogger(__name__)

_COLLECTION = "users"
_SUBCOLLECTION = "settings"
_PUSH_TOKENS_COLLECTION = "pushTokens"


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

    async def get_itad_country(self, uid: str) -> str | None:
        doc = await self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, "country")
        if doc is None:
            return None
        return doc.get("country_code")

    async def update_itad_country(self, uid: str, country: str) -> None:
        await self.set_subdoc(
            _COLLECTION, uid, _SUBCOLLECTION, "country", {"country_code": country}
        )

    async def delete_all(self, uid: str) -> None:
        await self.delete_subdoc(_COLLECTION, uid, _SUBCOLLECTION, "notifications")
        await self.remove_all_push_tokens(uid)

    # ------------------------------------------------------------------
    # Push notification tokens (top-level collection for bulk querying)
    # ------------------------------------------------------------------

    async def register_push_token(self, uid: str, expo_token: str, platform: str) -> str:
        token_id = f"{platform}_{uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        data: dict[str, Any] = {
            "uid": uid,
            "token_type": "expo",
            "expo_token": expo_token,
            "platform": platform,
            "created_at": now,
            "updated_at": now,
        }
        await self._db.collection(_PUSH_TOKENS_COLLECTION).document(token_id).set(data)

        # Clean up stale token docs for the same user (keep only one per platform)
        try:
            existing = (
                await self._db.collection(_PUSH_TOKENS_COLLECTION)
                .where("uid", "==", uid)
                .where("platform", "==", platform)
                .get()
            )
            for doc in existing:
                if doc.id != token_id:
                    await doc.reference.delete()
        except Exception:
            logger.warning("Failed to clean stale push tokens for uid=%s", uid)

        return token_id

    async def remove_push_token(self, uid: str, token_id: str) -> None:
        ref = self._db.collection(_PUSH_TOKENS_COLLECTION).document(token_id)
        doc = await ref.get()
        if doc.exists and doc.to_dict().get("uid") == uid:
            await ref.delete()

    async def remove_all_push_tokens(self, uid: str) -> None:
        try:
            docs = await self._db.collection(_PUSH_TOKENS_COLLECTION).where("uid", "==", uid).get()
            for doc in docs:
                await doc.reference.delete()
        except Exception:
            logger.warning("Failed to remove all push tokens for uid=%s", uid)

    async def get_all_push_tokens_with_prefs(
        self,
    ) -> list[dict[str, Any]]:
        tokens_snapshot = await self._db.collection(_PUSH_TOKENS_COLLECTION).stream()
        if not tokens_snapshot:
            return []

        from contextlib import suppress

        uid_to_token: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for doc in tokens_snapshot:
            token_data = doc.to_dict() or {}
            uid = token_data.get("uid", "")
            if not uid:
                continue
            if uid not in uid_to_token:
                uid_to_token[uid] = []
            uid_to_token[uid].append((doc.id, token_data))

        result: list[dict[str, Any]] = []
        for uid, tokens in uid_to_token.items():
            prefs_doc = await self.get_subdoc(_COLLECTION, uid, _SUBCOLLECTION, "notifications")
            if prefs_doc is None:
                continue
            prefs = prefs_doc.get("preferences") or {}
            if not prefs.get("dealsEnabled", False):
                # Remove stale tokens from top-level collection
                for token_id, _token in tokens:
                    with suppress(Exception):
                        await (
                            self._db.collection(_PUSH_TOKENS_COLLECTION).document(token_id).delete()
                        )
                continue
            for _token_id, token in tokens:
                result.append(
                    {
                        "uid": uid,
                        "expo_token": token["expo_token"],
                        "platform": token.get("platform", "ios"),
                    }
                )
        return result

    # ------------------------------------------------------------------
    # Deal alert tracking
    # ------------------------------------------------------------------

    async def get_deal_alert(self, uid: str, game_id: str) -> dict[str, Any] | None:
        doc = await self.get_subdoc(_COLLECTION, uid, "dealAlerts", game_id.replace("/", "_"))
        if doc is None:
            return None
        return {k: v for k, v in doc.items() if k != "__doc_id"}

    async def save_deal_alert(self, uid: str, game_id: str, alert_data: dict[str, Any]) -> None:
        await self.set_subdoc(
            _COLLECTION,
            uid,
            "dealAlerts",
            game_id.replace("/", "_"),
            {**alert_data, "updated_at": datetime.now(UTC).isoformat()},
        )
