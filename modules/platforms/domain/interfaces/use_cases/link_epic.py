"""Interface for the link Epic Games use case."""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class ILinkEpicUseCase(ABC):
    """Contract for linking an Epic Games account via OAuth2 authorization code."""

    @abstractmethod
    async def execute(self, uid: str, code: str) -> LinkedPlatform:
        """Exchange the authorization code and link the Epic Games account.

        Args:
            uid: Firebase user ID.
            code: Short-lived authorization code from the Epic login callback.

        Returns:
            The newly created LinkedPlatform entry.

        Raises:
            PlatformAlreadyLinkedException: If Epic is already linked.
        """
        ...
