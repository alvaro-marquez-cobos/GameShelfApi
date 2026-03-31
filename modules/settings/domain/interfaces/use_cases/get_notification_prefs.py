"""Interface for get notification preferences use case."""

from abc import ABC, abstractmethod
from typing import Any


class IGetNotificationPrefsUseCase(ABC):
    """Contract for retrieving user notification preferences."""

    @abstractmethod
    async def execute(self, uid: str) -> dict[str, Any]:
        """Return notification preferences for the user."""
        ...
