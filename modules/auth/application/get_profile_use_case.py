"""Use case for retrieving the authenticated user's profile."""

from typing import Any

from modules.auth.domain.exceptions import UserNotFoundException
from modules.auth.domain.interfaces.use_cases.get_profile import IGetProfileUseCase
from shared.domain.interfaces.user_repository import IUserRepository


class GetProfileUseCase(IGetProfileUseCase):
    """Fetches the user profile from the repository, raising if not found."""
    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, uid: str) -> dict[str, Any]:
        profile = await self._user_repository.find_by_uid(uid)
        if profile is None:
            raise UserNotFoundException(uid)
        return profile
