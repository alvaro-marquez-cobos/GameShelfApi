"""Interface for sourcing a user's Steam library as normalized LibraryGames."""

from abc import ABC, abstractmethod

from shared.domain.entities.library_game import LibraryGame


class ISteamLibrarySource(ABC):
    """Contract for fetching a user's owned Steam games.

    Implementations adapt the Steam Web API into generic ``LibraryGame``
    instances so the library module does not depend on Steam-specific
    entities.
    """

    @abstractmethod
    async def get_owned_games(self, steam_id: str) -> list[LibraryGame]:
        """Return all games owned by the given Steam user as ``LibraryGame``s."""
        ...
