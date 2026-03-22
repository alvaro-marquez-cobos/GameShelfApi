"""Epic Games platform domain entities."""

from dataclasses import dataclass, field


@dataclass
class EpicAuthToken:
    """OAuth2 token pair returned by the Epic Games auth service.

    Attributes:
        access_token: Short-lived bearer token for API requests.
        refresh_token: Long-lived token to obtain new access tokens.
        account_id: Epic account identifier for the authenticated user.
        display_name: Human-readable Epic display name.
        expires_at: ISO 8601 expiry datetime string for the access token.
    """

    access_token: str
    refresh_token: str
    account_id: str
    display_name: str = ""
    expires_at: str = ""


@dataclass
class EpicGame:
    """A game entry from the Epic Games library.

    Attributes:
        app_name: Unique artifact/app identifier on Epic.
        namespace: Epic catalog namespace the game belongs to.
        catalog_item_id: Catalog item identifier (used for enrichment).
    """

    app_name: str
    namespace: str
    catalog_item_id: str


@dataclass
class EpicCatalogItem:
    """Enriched catalog metadata for an Epic Games title.

    Attributes:
        id: Catalog item identifier.
        title: Display title of the game.
        description: Short description of the game.
        key_images: List of image objects with ``type`` and ``url`` fields.
        categories: Category slugs (e.g. "games/edition/base").
        developer: Developer name, if available.
    """

    id: str
    title: str
    description: str = ""
    key_images: list[dict[str, str]] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    developer: str = ""
