"""Remove from wishlist use case."""

from modules.wishlist.domain.exceptions import WishlistItemNotFoundException
from modules.wishlist.domain.interfaces.repositories.i_wishlist_repository import (
    IWishlistRepository,
)
from modules.wishlist.domain.interfaces.use_cases.remove_from_wishlist import (
    IRemoveFromWishlistUseCase,
)


class RemoveFromWishlistUseCase(IRemoveFromWishlistUseCase):
    """Remove a game from the user's wishlist, raising if not found."""

    def __init__(self, repo: IWishlistRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str, game_id: str) -> None:
        if not await self._repo.is_in_wishlist(uid, game_id):
            raise WishlistItemNotFoundException(game_id)
        await self._repo.remove(uid, game_id)
