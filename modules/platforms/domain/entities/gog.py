"""GOG platform domain entities."""

from dataclasses import dataclass


@dataclass
class GogAuthToken:
    """OAuth2 token pair returned by the GOG auth service.

    Attributes:
        access_token: Short-lived bearer token for API requests.
        refresh_token: Long-lived token to obtain new access tokens.
        user_id: GOG user identifier for the authenticated user.
        expires_at: ISO 8601 expiry datetime string for the access token.
    """

    access_token: str
    refresh_token: str
    user_id: str = ""
    expires_at: str = ""


@dataclass
class GogGame:
    """A game entry from the GOG user library.

    Attributes:
        id: GOG product identifier.
        title: Display title of the game.
        image_url: URL to the game's cover image.
        platform_id: Platform identifier string (always "gog").
    """

    id: str
    title: str
    image_url: str = ""
    platform_id: str = "gog"
