"""Use case: retrieve all platforms linked to a user account."""

from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.use_cases.get_linked_platforms import (
    IGetLinkedPlatformsUseCase,
)
from shared.domain.entities.linked_platform import LinkedPlatform


class GetLinkedPlatformsUseCase(IGetLinkedPlatformsUseCase):
    """Return all platforms linked to the given user."""

    def __init__(self, repo: IPlatformRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str) -> list[LinkedPlatform]:
        return await self._repo.get_linked(uid)
