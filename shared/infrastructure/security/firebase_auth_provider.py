import asyncio
from typing import Any

from firebase_admin import auth

from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.exceptions import UnauthorizedException
from shared.infrastructure.security.firebase_client import get_firebase_app


class FirebaseAuthProvider(IFirebaseAuthProvider):
    async def verify_token(self, id_token: str) -> dict[str, Any]:
        try:
            app = get_firebase_app()
            decoded = await asyncio.to_thread(auth.verify_id_token, id_token, app=app)
            return dict(decoded)
        except Exception as exc:
            raise UnauthorizedException("Invalid or expired token") from exc

    async def delete_user(self, uid: str) -> None:
        try:
            app = get_firebase_app()
            await asyncio.to_thread(auth.delete_user, uid, app=app)
        except Exception as exc:
            raise UnauthorizedException(f"Failed to delete user {uid}") from exc
