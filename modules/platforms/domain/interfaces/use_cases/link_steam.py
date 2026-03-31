"""Interface for the link Steam use case."""

from abc import ABC, abstractmethod

from shared.domain.entities.linked_platform import LinkedPlatform


class ILinkSteamUseCase(ABC):
    """Contract for linking a Steam account via OpenID callback."""

    @abstractmethod
    async def execute(self, uid: str, openid_params: dict[str, str]) -> LinkedPlatform:
        """Verify the OpenID callback and link the Steam account.

        Args:
            uid: Firebase user ID.
            openid_params: Raw query parameters from the Steam OpenID callback.

        Returns:
            The newly created LinkedPlatform entry.

        Raises:
            BadRequestException: If the OpenID verification fails.
            PlatformAlreadyLinkedException: If Steam is already linked.
        """
        ...
