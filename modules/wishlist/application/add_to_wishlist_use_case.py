"""Add to wishlist use case."""

from modules.wishlist.domain.entities.wishlist_item import WishlistItem
from modules.wishlist.domain.exceptions import WishlistItemAlreadyExistsException
from modules.wishlist.domain.interfaces.repositories.i_wishlist_repository import (
    IWishlistRepository,
)
from modules.wishlist.domain.interfaces.use_cases.add_to_wishlist import IAddToWishlistUseCase


class AddToWishlistUseCase(IAddToWishlistUseCase):
    """Add a game to the user's wishlist, rejecting duplicates."""

    def __init__(self, repo: IWishlistRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str, item: WishlistItem) -> None:
        if await self._repo.is_in_wishlist(uid, item.game_id):
            raise WishlistItemAlreadyExistsException(item.game_id)
        await self._repo.add(uid, item)
