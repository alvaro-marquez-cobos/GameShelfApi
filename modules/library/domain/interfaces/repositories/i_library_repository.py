"""Interface for user library persistence operations."""

from abc import ABC, abstractmethod

from modules.library.domain.entities.library_game import LibraryGame


class ILibraryRepository(ABC):
    """Contract for storing and retrieving the user's game library."""

    @abstractmethod
    async def get_games(self, uid: str) -> list[LibraryGame]:
        """Return all games in the user's library."""
        ...

    @abstractmethod
    async def get_game(self, uid: str, game_id: str) -> LibraryGame | None:
        """Return a single game by ID, or None if not found."""
        ...

    @abstractmethod
    async def upsert_games(self, uid: str, games: list[LibraryGame]) -> None:
        """Create or update multiple game entries in the user's library."""
        ...
