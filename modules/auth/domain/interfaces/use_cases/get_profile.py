"""Interface for the get profile use case."""

from abc import ABC, abstractmethod
from typing import Any


class IGetProfileUseCase(ABC):
    """Contract for retrieving a user's profile data."""

    @abstractmethod
    async def execute(self, uid: str) -> dict[str, Any]:
        """Fetch the user profile for the given UID.

        Raises:
            UserNotFoundException: If no profile exists for the UID.
        """
        ...
