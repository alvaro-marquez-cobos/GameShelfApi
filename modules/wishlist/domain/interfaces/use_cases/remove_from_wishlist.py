"""Interface for the remove from wishlist use case."""

from abc import ABC, abstractmethod


class IRemoveFromWishlistUseCase(ABC):
    """Contract for removing a game from the user's wishlist."""

    @abstractmethod
    async def execute(self, uid: str, game_id: str) -> None:
        """Remove a game from the wishlist.

        Raises:
            WishlistItemNotFoundException: if the game is not in the wishlist.
        """
        ...
