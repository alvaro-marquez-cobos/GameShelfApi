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

    @abstractmethod
    async def get_game(self, uid: str, game_id: str) -> LibraryGame | None:
        """Return a single library entry for the user, or ``None`` if absent."""
        ...

    @abstractmethod
    async def get_most_played(self, uid: str, limit: int) -> list[LibraryGame]:
        """Return the top ``limit`` games ordered by playtime descending.

        Implementations should use a native query rather than loading the full
        library, so reads are bounded to ``limit`` documents.
        """
        ...
