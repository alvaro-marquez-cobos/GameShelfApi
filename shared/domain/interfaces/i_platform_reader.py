"""Cross-module interface for reading linked platform data.

Allows modules like library and home to query platform links without
importing directly from the platforms module.
"""

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform


class IPlatformReader(ABC):
    """Read-only cross-module access to the user's linked platforms."""

    @abstractmethod
    async def get_linked_platforms(self, uid: str) -> list[LinkedPlatform]:
        """Return all platforms currently linked to the user's account."""
        ...

    @abstractmethod
    async def get_platform_tokens(self, uid: str, platform: Platform) -> dict[str, Any] | None:
        """Return stored OAuth tokens for a platform, or None if not linked."""
        ...

    @abstractmethod
    async def get_linked_with_tokens(self, uid: str) -> list[tuple[LinkedPlatform, dict[str, Any]]]:
        """Return all linked platforms together with their stored tokens.

        Reads the platforms subcollection once and extracts both the platform
        metadata and the OAuth tokens from the same documents, avoiding the
        extra per-platform reads that result from calling get_platform_tokens()
        separately for each linked platform.
        """
        ...
