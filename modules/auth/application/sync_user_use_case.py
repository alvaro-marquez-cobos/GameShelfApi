from typing import Any

from modules.auth.domain.interfaces.use_cases.sync_user import ISyncUserUseCase
from shared.domain.entities.user import AuthenticatedUser
from shared.domain.interfaces.user_repository import IUserRepository


class SyncUserUseCase(ISyncUserUseCase):
    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, user: AuthenticatedUser) -> dict[str, Any]:
        return await self._user_repository.upsert(user)
