"""Interface for platform account persistence operations."""

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


class IPlatformRepository(ABC):
    """Contract for storing and retrieving linked platform accounts."""

    @abstractmethod
    async def get_linked(self, uid: str) -> list[LinkedPlatform]:
        """Return all platforms linked to the user's account."""
        ...

    @abstractmethod
    async def link(self, uid: str, platform_data: LinkedPlatform) -> None:
        """Persist a new platform link for the user."""
        ...

    @abstractmethod
    async def unlink(self, uid: str, platform: Platform) -> None:
        """Remove a platform link from the user's account."""
        ...

    @abstractmethod
    async def get_tokens(self, uid: str, platform: Platform) -> dict[str, Any] | None:
        """Return the stored OAuth tokens for a platform, or None."""
        ...

    @abstractmethod
    async def store_tokens(self, uid: str, platform: Platform, tokens: dict[str, Any]) -> None:
        """Persist OAuth tokens for a linked platform."""
        ...
