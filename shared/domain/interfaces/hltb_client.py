"""Interface for the HowLongToBeat game duration client."""

from abc import ABC, abstractmethod

from modules.games.domain.entities.hltb import HltbResult


class IHltbClient(ABC):
    """Contract for fetching game completion times from HowLongToBeat."""

    @abstractmethod
    async def get_game_duration(self, game_title: str) -> HltbResult | None:
        """Fetch completion time data for a game by title.

        Args:
            game_title: The game title to search for.

        Returns:
            An ``HltbResult`` with main story, main+extra, and completionist
            hours, or None if no data is found.
        """
        ...
