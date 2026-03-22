"""Use case for permanently deleting a user account.

Orchestrates the full deletion flow: module cleanup handlers, user
document removal, and Firebase account deletion.
"""

from modules.auth.domain.exceptions import AccountDeletionException
from modules.auth.domain.interfaces.use_cases.delete_account import IDeleteAccountUseCase
from shared.domain.interfaces.cleanup_registry import ICleanupRegistry
from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.domain.interfaces.user_repository import IUserRepository


class DeleteAccountUseCase(IDeleteAccountUseCase):
    """Deletes user data across all modules and removes the Firebase account."""

    def __init__(
        self,
        cleanup_registry: ICleanupRegistry,
        user_repository: IUserRepository,
        firebase_auth: IFirebaseAuthProvider,
    ) -> None:
        self._cleanup_registry = cleanup_registry
        self._user_repository = user_repository
        self._firebase_auth = firebase_auth

    async def execute(self, uid: str) -> None:
        try:
            await self._cleanup_registry.execute_all(uid)
            await self._user_repository.delete(uid)
            await self._firebase_auth.delete_user(uid)
        except Exception as exc:
            raise AccountDeletionException(f"Failed to delete account for {uid}") from exc
