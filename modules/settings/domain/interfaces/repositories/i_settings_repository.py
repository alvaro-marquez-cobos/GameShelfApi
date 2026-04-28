"""Interface for settings persistence operations."""

from abc import ABC, abstractmethod
from typing import Any


class ISettingsRepository(ABC):
    """Contract for storing and retrieving user settings."""

    @abstractmethod
    async def get_notification_prefs(self, uid: str) -> dict[str, Any] | None:
        """Return notification preferences for a user, or None."""
        ...

    @abstractmethod
    async def update_notification_prefs(self, uid: str, prefs: dict[str, Any]) -> None:
        """Update notification preferences for a user."""
        ...

    @abstractmethod
    async def get_itad_country(self, uid: str) -> str | None:
        """Return the ITAD country preference for a user, or None if not set."""
        ...

    @abstractmethod
    async def update_itad_country(self, uid: str, country: str) -> None:
        """Update the ITAD country preference for a user.

        Args:
            uid: Firebase UID of the user.
            country: ISO 3166-1 alpha-2 country code (e.g. "ES", "MX").
        """
        ...

    @abstractmethod
    async def delete_all(self, uid: str) -> None:
        """Remove all settings for a user (cleanup on account deletion)."""
        ...
