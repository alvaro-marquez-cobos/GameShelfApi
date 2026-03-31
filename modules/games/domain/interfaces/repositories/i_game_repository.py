"""Interface for game metadata persistence operations."""

from abc import ABC, abstractmethod
from typing import Any


class IGameRepository(ABC):
    """Contract for storing and retrieving enriched game documents."""

    @abstractmethod
    async def get_game(self, game_id: str) -> dict[str, Any] | None:
        """Return the game document, or None if not found."""
        ...

    @abstractmethod
    async def update_steam_app_id(self, game_id: str, steam_app_id: int) -> None:
        """Persist a resolved Steam App ID on an existing game document."""
        ...
