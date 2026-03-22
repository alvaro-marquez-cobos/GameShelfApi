"""Interface for the logout use case."""

from abc import ABC, abstractmethod


class ILogoutUseCase(ABC):
    """Contract for invalidating an active session token."""

    @abstractmethod
    async def execute(self, token: str) -> None:
        """Blacklist the given token so it can no longer be used for authentication."""
        ...
