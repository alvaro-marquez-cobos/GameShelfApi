"""Interface for linking Epic using GDPR exported JSON."""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class ILinkEpicGdprUseCase(ABC):
    """Contract for linking Epic account and importing games from GDPR export."""

    @abstractmethod
    async def execute(self, uid: str, json_content: str) -> LinkedPlatform:
        """Parse GDPR JSON, import games, and persist linked platform entry."""
        ...
