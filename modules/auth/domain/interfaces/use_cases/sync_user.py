"""Interface for the sync user use case."""

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.entities.user import AuthenticatedUser


class ISyncUserUseCase(ABC):
    """Contract for synchronizing a user profile after login.

    Creates the user document on first login or updates it with the
    latest identity provider data on subsequent logins.
    """

    @abstractmethod
    async def execute(self, user: AuthenticatedUser) -> dict[str, Any]:
        """Persist the authenticated user's profile and return the stored data."""
        ...
