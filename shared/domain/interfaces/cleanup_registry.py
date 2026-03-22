"""Interface for the cleanup registry used during account deletion."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any


class ICleanupRegistry(ABC):
    """Registry of cleanup handlers invoked when a user account is deleted.

    Modules register their own cleanup logic so that account deletion
    can cascade across module boundaries without direct cross-module imports.
    """

    @abstractmethod
    def register(self, name: str, handler: Callable[[str], Coroutine[Any, Any, None]]) -> None:
        """Register a named cleanup handler for account deletion.

        Args:
            name: Unique identifier for the handler (e.g. module name).
            handler: Async callable that receives the user's UID.
        """
        ...

    @abstractmethod
    async def execute_all(self, uid: str) -> None:
        """Run all registered cleanup handlers concurrently for the given user.

        Args:
            uid: Firebase UID of the user being deleted.
        """
        ...
