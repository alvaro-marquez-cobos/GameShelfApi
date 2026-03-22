"""PlayStation Network platform domain entities."""

from dataclasses import dataclass


@dataclass
class PsnAuthToken:
    """OAuth2 token pair returned by the PSN auth service.

    Attributes:
        access_token: Short-lived JWT bearer token for API requests.
        refresh_token: Long-lived token to obtain new access tokens.
        account_id: PSN account identifier (online ID) for the user.
        expires_at: ISO 8601 expiry datetime string for the access token.
    """

    access_token: str
    refresh_token: str
    account_id: str = ""
    expires_at: str = ""


@dataclass
class PsnGame:
    """A game entry from the PSN user's played titles list.

    Attributes:
        title_id: PSN title identifier (e.g. "CUSA12345_00").
        name: Display name of the game.
        image_url: URL to the game's cover image.
        play_duration_minutes: Total playtime in minutes parsed from ISO 8601.
        first_played_at: ISO 8601 datetime of the first play session.
        last_played_at: ISO 8601 datetime of the most recent play session.
        platform: Platform string (e.g. "PS4", "PS5").
    """

    title_id: str
    name: str
    image_url: str = ""
    play_duration_minutes: int = 0
    first_played_at: str = ""
    last_played_at: str = ""
    platform: str = ""
