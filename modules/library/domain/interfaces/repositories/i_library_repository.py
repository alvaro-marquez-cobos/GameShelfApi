"""Interface for user library persistence operations."""

from abc import abstractmethod

from shared.domain.entities.library_game import LibraryGame
from shared.domain.interfaces.i_library_reader import ILibraryReader


class ILibraryRepository(ILibraryReader):
    """Contract for storing and retrieving the user's game library."""

    @abstractmethod
    async def upsert_games(self, uid: str, games: list[LibraryGame]) -> None:
        """Create or update multiple game entries in the user's library."""
        ...
