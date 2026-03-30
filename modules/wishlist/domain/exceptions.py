"""Wishlist module domain exceptions."""

from shared.exceptions import ConflictException, NotFoundException


class WishlistItemNotFoundException(NotFoundException):
    """Raised when a game is not found in the user's wishlist."""

    def __init__(self, game_id: str) -> None:
        super().__init__(f"Game '{game_id}' is not in the wishlist")


class WishlistItemAlreadyExistsException(ConflictException):
    """Raised when attempting to add a game already on the wishlist."""

    def __init__(self, game_id: str) -> None:
        super().__init__(f"Game '{game_id}' is already in the wishlist")
