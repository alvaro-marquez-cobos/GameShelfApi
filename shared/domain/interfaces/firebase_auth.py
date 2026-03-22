"""Interface for Firebase Authentication operations."""

from abc import ABC, abstractmethod
from typing import Any


class IFirebaseAuthProvider(ABC):
    """Contract for verifying tokens and managing Firebase user accounts."""
    @abstractmethod
    async def verify_token(self, id_token: str) -> dict[str, Any]:
        """Verify a Firebase ID token and return the decoded claims.

        Raises:
            UnauthorizedException: If the token is invalid or expired.
        """
        ...

    @abstractmethod
    async def delete_user(self, uid: str) -> None:
        """Delete a user account from Firebase Authentication.

        Raises:
            UnauthorizedException: If the deletion fails.
        """
        ...
