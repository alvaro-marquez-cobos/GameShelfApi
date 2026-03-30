"""Interface for the check wishlist use case."""

from abc import ABC, abstractmethod


class ICheckWishlistUseCase(ABC):
    """Contract for checking whether a game is on the user's wishlist."""

    @abstractmethod
    async def execute(self, uid: str, game_id: str) -> bool:
        """Return True if the game is currently in the user's wishlist."""
        ...
