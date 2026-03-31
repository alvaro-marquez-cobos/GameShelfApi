"""Use case: unlink a gaming platform from a user account."""

from modules.platforms.domain.exceptions import PlatformNotFoundException
from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.use_cases.unlink_platform import (
    IUnlinkPlatformUseCase,
)
from shared.domain.enums.platform import Platform


class UnlinkPlatformUseCase(IUnlinkPlatformUseCase):
    """Remove a platform link after verifying it exists."""

    def __init__(self, repo: IPlatformRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str, platform: Platform) -> None:
        existing = await self._repo.get_linked(uid)
        if not any(lp.platform == platform for lp in existing):
            raise PlatformNotFoundException(platform.value)
        await self._repo.unlink(uid, platform)
