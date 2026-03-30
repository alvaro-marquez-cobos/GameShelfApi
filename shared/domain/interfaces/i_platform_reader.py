"""Cross-module interface for reading linked platform data.

Allows modules like library and home to query platform links without
importing directly from the platforms module.
"""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class IPlatformReader(ABC):
    """Read-only cross-module access to the user's linked platforms."""

    @abstractmethod
    async def get_linked_platforms(self, uid: str) -> list[LinkedPlatform]:
        """Return all platforms currently linked to the user's account."""
        ...
