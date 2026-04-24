"""Interface for the get game detail use case."""

from abc import ABC, abstractmethod

from modules.games.domain.entities.game_detail import GameDetail
from shared.domain.enums.platform import Platform


class IGetGameDetailUseCase(ABC):
    """Contract for retrieving fully enriched game detail."""

    @abstractmethod
    async def execute(
        self,
        uid: str,
        game_id: str,
        platform: Platform | None = None,
    ) -> GameDetail:
        """Return enriched game detail for the given game.

        Args:
            uid: Firebase UID of the requesting user.
            game_id: Deterministic library game ID (e.g. ``steam_570``).
            platform: Optional platform hint from the client to guide
                enrichment when the game is not in the user's library.

        Returns:
            A ``GameDetail`` with as much enrichment as available.
            Fields from unavailable services are None or empty.
        """
        ...
