"""Interface for the add to wishlist use case."""

from abc import ABC, abstractmethod

from modules.wishlist.domain.entities.wishlist_item import WishlistItem


class IAddToWishlistUseCase(ABC):
    """Contract for adding a game to the user's wishlist."""

    @abstractmethod
    async def execute(self, uid: str, item: WishlistItem) -> None:
        """Add a game to the wishlist.

        Raises:
            WishlistItemAlreadyExistsException: if the game is already present.
        """
        ...
