"""Interface for update notification preferences use case."""

from abc import ABC, abstractmethod
from typing import Any


class IUpdateNotificationPrefsUseCase(ABC):
    """Contract for updating user notification preferences."""

    @abstractmethod
    async def execute(self, uid: str, prefs: dict[str, Any]) -> None:
        """Update notification preferences for the user."""
        ...
