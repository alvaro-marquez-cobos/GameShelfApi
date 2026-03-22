"""Interface for the ProtonDB compatibility rating client."""

from abc import ABC, abstractmethod

from modules.games.domain.entities.protondb import ProtonDbRating


class IProtonDbClient(ABC):
    """Contract for fetching ProtonDB Linux/Proton compatibility ratings."""

    @abstractmethod
    async def get_compatibility_rating(self, steam_app_id: str) -> ProtonDbRating | None:
        """Fetch the ProtonDB rating for a Steam application.

        Args:
            steam_app_id: Numeric Steam app ID as a string.

        Returns:
            A ``ProtonDbRating`` instance, or None if the game is not in ProtonDB
            or the endpoint is unavailable.
        """
        ...
