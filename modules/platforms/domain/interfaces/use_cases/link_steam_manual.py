"""Interface for linking Steam by profile URL, vanity, or SteamID64."""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class ILinkSteamManualUseCase(ABC):
    """Contract for linking a Steam account without OpenID callback."""

    @abstractmethod
    async def execute(self, uid: str, profile_url_or_id: str) -> LinkedPlatform:
        """Resolve SteamID64 from input and link the account."""
        ...
