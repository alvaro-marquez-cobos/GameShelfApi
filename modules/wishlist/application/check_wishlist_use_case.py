"""Check wishlist use case."""

from modules.wishlist.domain.interfaces.repositories.i_wishlist_repository import (
    IWishlistRepository,
)
from modules.wishlist.domain.interfaces.use_cases.check_wishlist import ICheckWishlistUseCase


class CheckWishlistUseCase(ICheckWishlistUseCase):
    """Return whether a game is on the user's wishlist."""

    def __init__(self, repo: IWishlistRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str, game_id: str) -> bool:
        return await self._repo.is_in_wishlist(uid, game_id)
