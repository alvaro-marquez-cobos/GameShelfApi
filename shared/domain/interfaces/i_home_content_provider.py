"""Interface for providing aggregated content for the home screen."""

from abc import ABC, abstractmethod

from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.popular_game import PopularGame


class IHomeContentProvider(ABC):
    """Contract for sourcing home-screen content from external platforms.

    Implementations adapt platform-specific clients (e.g. Steam) into
    generic home-screen DTOs so the home module stays decoupled from any
    concrete platform.
    """

    @abstractmethod
    async def get_recently_played(self, uid: str) -> list[LibraryGame] | None:
        """Return the user's recently played games, or ``None`` if unavailable."""
        ...

    @abstractmethod
    async def get_globally_popular(self, limit: int) -> list[PopularGame]:
        """Return a list of globally popular games."""
        ...
