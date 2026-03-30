"""Cross-module interface for reading wishlist data.

Allows modules like search and games to check wishlist membership without
importing directly from the wishlist module.
"""

from abc import ABC, abstractmethod


class IWishlistReader(ABC):
    """Read-only cross-module access to the user's wishlist."""

    @abstractmethod
    async def is_in_wishlist(self, uid: str, game_id: str) -> bool:
        """Return True if the game is in the user's wishlist."""
        ...

    @abstractmethod
    async def get_wishlist_ids(self, uid: str) -> set[str]:
        """Return the set of game IDs on the user's wishlist."""
        ...
