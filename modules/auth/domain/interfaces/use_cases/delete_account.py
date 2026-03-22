"""Interface for the delete account use case."""

from abc import ABC, abstractmethod


class IDeleteAccountUseCase(ABC):
    """Contract for permanently deleting a user account and all associated data."""

    @abstractmethod
    async def execute(self, uid: str) -> None:
        """Delete the user's data across all modules and remove the Firebase account.

        Raises:
            AccountDeletionException: If any step of the deletion fails.
        """
        ...
