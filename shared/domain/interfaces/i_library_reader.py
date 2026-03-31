"""Cross-module interface for reading library data.

Allows modules like home to query library data without importing directly
from the library module.
"""

from abc import ABC, abstractmethod

from shared.domain.entities.library_game import LibraryGame


class ILibraryReader(ABC):
    """Read-only cross-module access to the user's game library."""

    @abstractmethod
    async def get_games(self, uid: str) -> list[LibraryGame]:
        """Return all games in the user's library."""
        ...
