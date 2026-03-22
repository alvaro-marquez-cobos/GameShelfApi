"""Interface for user persistence operations."""

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.entities.user import AuthenticatedUser


class IUserRepository(ABC):
    """Contract for storing and retrieving user profile data."""

    @abstractmethod
    async def find_by_uid(self, uid: str) -> dict[str, Any] | None:
        """Retrieve a user document by UID, or None if it does not exist."""
        ...

    @abstractmethod
    async def upsert(self, user: AuthenticatedUser) -> dict[str, Any]:
        """Create or update a user document, returning the persisted data."""
        ...

    @abstractmethod
    async def delete(self, uid: str) -> None:
        """Permanently remove the user document for the given UID."""
        ...
