"""IsThereAnyDeal game info, deal, and search result entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Deal:
    """A current store price entry from IsThereAnyDeal.

    Args:
        id: Unique identifier for this deal entry (shop_id + index).
        store_name: Human-readable store name.
        price: Current sale price.
        regular_price: Regular (non-sale) price.
        discount: Discount percentage (0-100).
        url: Direct link to the store listing.
        currency: ISO 4217 currency code (e.g. "USD").
    """

    id: str
    store_name: str
    price: float
    regular_price: float
    discount: int
    url: str
    currency: str


@dataclass(frozen=True)
class ItadGameInfo:
    """Basic metadata for a game on IsThereAnyDeal.

    Args:
        id: ITAD UUID for the game.
        title: Canonical game title.
        steam_app_id: Steam app ID if available, otherwise None.
        cover_url: URL to the game cover image (banner300 or banner400).
    """

    id: str
    title: str
    steam_app_id: int | None
    cover_url: str


@dataclass(frozen=True)
class ItadSearchResult:
    """A game result returned by the ITAD search endpoint.

    Args:
        id: ITAD UUID for the game.
        title: Game title.
        cover_url: Cover image URL.
        steam_app_id: Steam app ID if enriched, otherwise None.
        game_type: ITAD game type (e.g., "game", "dlc"). Only present in /games/search/v1 results.
    """

    id: str
    title: str
    cover_url: str
    steam_app_id: int | None
    game_type: str | None = None
