"""Interface for the unlink platform use case."""

from abc import ABC, abstractmethod

from shared.domain.enums.platform import Platform


class IUnlinkPlatformUseCase(ABC):
    """Contract for unlinking a gaming platform from a user account."""

    @abstractmethod
    async def execute(self, uid: str, platform: Platform) -> None:
        """Remove the platform link from the user's account.

        Args:
            uid: Firebase user ID.
            platform: The platform to unlink.

        Raises:
            PlatformNotFoundException: If the platform is not currently linked.
        """
        ...
