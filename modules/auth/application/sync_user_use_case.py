"""Use case for synchronizing user profile data after authentication."""

from typing import Any

from modules.auth.domain.interfaces.use_cases.sync_user import ISyncUserUseCase
from shared.domain.entities.user import AuthenticatedUser
from shared.domain.interfaces.user_repository import IUserRepository


class SyncUserUseCase(ISyncUserUseCase):
    """Creates or updates the user document with the latest provider data."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, user: AuthenticatedUser) -> dict[str, Any]:
        return await self._user_repository.upsert(user)
