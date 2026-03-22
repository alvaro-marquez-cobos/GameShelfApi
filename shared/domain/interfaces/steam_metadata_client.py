"""Interface for the Steam Store metadata client."""

from abc import ABC, abstractmethod

from modules.games.domain.entities.steam import SteamAppDetails


class ISteamMetadataClient(ABC):
    """Contract for fetching game metadata from the Steam Store API."""

    @abstractmethod
    async def get_app_details(self, app_id: int) -> SteamAppDetails | None:
        """Fetch detailed metadata for a Steam application.

        Args:
            app_id: Steam application identifier.

        Returns:
            A ``SteamAppDetails`` instance or None if the app is not found.
        """
        ...

    @abstractmethod
    async def search_store(self, title: str) -> int | None:
        """Search the Steam Store for a game by title and return its app ID.

        Args:
            title: Game title to search for.

        Returns:
            The Steam app ID of the best match, or None if no match is found.
        """
        ...
