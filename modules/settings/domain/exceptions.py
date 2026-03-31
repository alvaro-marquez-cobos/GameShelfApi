"""Settings domain exceptions."""

from shared.exceptions import AppException


class SettingsException(AppException):
    """Base exception for settings operations."""


class NotificationPrefsNotFoundException(SettingsException):
    """Raised when notification preferences are not found for a user."""

    def __init__(self, uid: str) -> None:
        super().__init__(f"Notification preferences not found for user {uid}")
