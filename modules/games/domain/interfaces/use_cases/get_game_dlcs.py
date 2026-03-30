"""Interface for the get game DLCs use case."""

from abc import ABC, abstractmethod

from modules.games.domain.entities.game_detail import DlcDetail


class IGetGameDlcsUseCase(ABC):
    """Contract for retrieving DLC details for a Steam game."""

    @abstractmethod
    async def execute(self, uid: str, game_id: str) -> list[DlcDetail]:
        """Return DLC entries for the given game with ownership flags.

        Args:
            uid: Firebase UID of the requesting user.
            game_id: Deterministic library game ID (e.g. ``steam_570``).

        Returns:
            List of DLC details. Empty if no DLCs or steam_app_id unresolved.
        """
        ...
