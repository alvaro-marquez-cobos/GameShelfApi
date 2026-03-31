"""Interface for the link PSN use case."""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class ILinkPsnUseCase(ABC):
    """Contract for linking a PlayStation Network account via NPSSO token."""

    @abstractmethod
    async def execute(self, uid: str, npsso: str) -> LinkedPlatform:
        """Exchange the NPSSO token and link the PSN account.

        Args:
            uid: Firebase user ID.
            npsso: NPSSO cookie value from an active PlayStation session.

        Returns:
            The newly created LinkedPlatform entry.

        Raises:
            PlatformAlreadyLinkedException: If PSN is already linked.
        """
        ...
