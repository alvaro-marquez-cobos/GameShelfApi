"""Interface for the get wishlist use case."""

from abc import ABC, abstractmethod
from typing import Any

from modules.wishlist.domain.entities.wishlist_item import WishlistItem


class IGetWishlistUseCase(ABC):
    """Contract for retrieving wishlist items with deal enrichment."""

    @abstractmethod
    async def execute(
        self, uid: str, country: str | None = None
    ) -> list[tuple[WishlistItem, list[Any]]]:
        """Return all wishlist items paired with current ITAD deals.

        Each tuple contains the wishlist item and a (possibly empty) list of
        deals. If ITAD enrichment fails for a specific item the list is empty.

        Args:
            uid: Firebase UID of the requesting user.
            country: ISO 3166-1 alpha-2 country code for pricing lookups.

        Returns:
            List of (WishlistItem, deals) tuples.
        """
        ...
