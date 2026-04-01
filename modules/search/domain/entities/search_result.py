"""Domain entity for a single game search result."""

from dataclasses import dataclass, field

from shared.domain.enums.platform import Platform


@dataclass
class SearchResult:
    """A game search result enriched with user-specific context flags.

    Attributes:
        id: ITAD UUID for the game.
        title: Game title.
        cover_url: Cover image URL.
        steam_app_id: Steam app ID if available, otherwise None.
        is_owned: Whether the user already owns this game in their library.
        owned_platforms: Platforms on which the user owns this game.
        is_in_wishlist: Whether the user has this game on their wishlist.
    """

    id: str
    title: str
    cover_url: str
    steam_app_id: int | None
    is_owned: bool = False
    owned_platforms: list[Platform] = field(default_factory=list)
    is_in_wishlist: bool = False
