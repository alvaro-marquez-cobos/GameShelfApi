"""Interface for the get linked platforms use case."""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class IGetLinkedPlatformsUseCase(ABC):
    """Contract for retrieving all platforms linked to a user account."""

    @abstractmethod
    async def execute(self, uid: str) -> list[LinkedPlatform]:
        """Return all platforms linked to the given user."""
        ...
