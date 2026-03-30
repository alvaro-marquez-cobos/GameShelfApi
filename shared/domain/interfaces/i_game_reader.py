"""Cross-module interface for reading owned game data.

Allows modules like search and home to query library data without
importing directly from the library module.
"""

from abc import ABC, abstractmethod


class IGameReader(ABC):
    """Read-only cross-module access to the user's owned games."""

    @abstractmethod
    async def get_owned_game_ids(self, uid: str) -> set[str]:
        """Return the set of game IDs owned by the user."""
        ...
