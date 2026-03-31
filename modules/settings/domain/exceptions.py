"""Settings domain exceptions."""

from shared.exceptions import AppException, NotFoundException


class SettingsException(AppException):
    """Base exception for settings operations."""

    def __init__(self, message: str = "Settings operation failed") -> None:
        super().__init__(500, "SETTINGS_ERROR", message)


class NotificationPrefsNotFoundException(NotFoundException):
    """Raised when notification preferences are not found for a user."""

    def __init__(self, uid: str) -> None:
        super().__init__(f"Notification preferences not found for user {uid}")
