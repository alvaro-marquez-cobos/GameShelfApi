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

    # ------------------------------------------------------------------
    # Push notification tokens
    # ------------------------------------------------------------------

    @abstractmethod
    async def register_push_token(self, uid: str, expo_token: str, platform: str) -> str:
        """Register or update a push notification token for the user.

        If an existing document with the same ``expo_token`` is found under
        ``users/{uid}/settings/pushTokens``, that document ID is reused so we
        don't create duplicates.  Otherwise a new subdocument is created with
        a UUID-based ID.

        Returns:
            The token document ID.
        """
        ...

    @abstractmethod
    async def remove_push_token(self, uid: str, token_id: str) -> None:
        """Remove a specific push notification token for the user."""
        ...

    @abstractmethod
    async def remove_all_push_tokens(self, uid: str) -> None:
        """Remove all push notification tokens for the user."""
        ...

    @abstractmethod
    async def get_all_push_tokens_with_prefs(
        self,
    ) -> list[dict[str, Any]]:
        """Return all active users with deal alerts enabled and at least one push token.

        Each dict contains ``uid``, ``expo_token`` and ``platform`` fields
        suitable for bulk notification dispatch by the DealChecker service.
        """
        ...

    # ------------------------------------------------------------------
    # Deal alert tracking
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_deal_alert(self, uid: str, game_id: str) -> dict[str, Any] | None:
        """Return deal alert data for a specific game, or None."""
        ...

    @abstractmethod
    async def save_deal_alert(self, uid: str, game_id: str, alert_data: dict[str, Any]) -> None:
        """Save or update deal alert tracking data for a game.

        Args:
            uid: Firebase UID of the user.
            game_id: The game identifier (e.g. ``steam_12345``).
            alert_data: Alert metadata including last_alert_price,
                historical_low_price, etc.
        """
        ...
