"""Interface for the link GOG use case."""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class ILinkGogUseCase(ABC):
    """Contract for linking a GOG account via OAuth2 authorization code."""

    @abstractmethod
    async def execute(self, uid: str, code: str) -> LinkedPlatform:
        """Exchange the authorization code and link the GOG account.

        Args:
            uid: Firebase user ID.
            code: Short-lived authorization code from the GOG login callback.

        Returns:
            The newly created LinkedPlatform entry.

        Raises:
            PlatformAlreadyLinkedException: If GOG is already linked.
        """
        ...
