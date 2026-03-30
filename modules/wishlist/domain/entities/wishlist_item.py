"""Domain entity representing a game on a user's wishlist."""

from dataclasses import dataclass

from shared.domain.enums.platform import Platform


@dataclass
class WishlistItem:
    """A single entry in the user's game wishlist.

    Attributes:
        game_id: Deterministic ID matching the library convention.
        title: Display title of the game.
        platform: Primary platform this game was wishlisted from.
        cover_url: URL of the cover image, or None if unavailable.
        added_at: ISO-8601 timestamp of when the item was added.
    """

    game_id: str
    title: str
    platform: Platform
    cover_url: str | None = None
    added_at: str = ""
