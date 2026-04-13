"""Interface for the get game detail use case."""

from abc import ABC, abstractmethod

from modules.games.domain.entities.game_detail import GameDetail


class IGetGameDetailUseCase(ABC):
    """Contract for retrieving fully enriched game detail."""

    @abstractmethod
    async def execute(self, uid: str, game_id: str) -> GameDetail:
        """Return enriched game detail for the given game.

        Args:
            uid: Firebase UID of the requesting user.
            game_id: Deterministic library game ID (e.g. ``steam_570``).

        Returns:
            A ``GameDetail`` with as much enrichment as available.
            Fields from unavailable services are None or empty.
        """
        ...
