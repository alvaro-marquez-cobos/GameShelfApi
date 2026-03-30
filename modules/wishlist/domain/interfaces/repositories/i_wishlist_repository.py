"""Interface for wishlist persistence operations."""

from abc import ABC, abstractmethod

from modules.wishlist.domain.entities.wishlist_item import WishlistItem


class IWishlistRepository(ABC):
    """Contract for storing and retrieving the user's wishlist."""

    @abstractmethod
    async def get_items(self, uid: str) -> list[WishlistItem]:
        """Return all items in the user's wishlist."""
        ...

    @abstractmethod
    async def add(self, uid: str, item: WishlistItem) -> None:
        """Add a game to the wishlist."""
        ...

    @abstractmethod
    async def remove(self, uid: str, game_id: str) -> None:
        """Remove a game from the wishlist."""
        ...

    @abstractmethod
    async def is_in_wishlist(self, uid: str, game_id: str) -> bool:
        """Return True if the game is currently in the user's wishlist."""
        ...
