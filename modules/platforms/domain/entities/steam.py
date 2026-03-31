"""Steam platform domain entities."""

from dataclasses import dataclass, field


@dataclass
class SteamGame:
    """A game from a Steam user's library or the global charts.

    Attributes:
        app_id: Steam application identifier.
        name: Display name of the game.
        playtime_forever: Total playtime across all sessions in minutes.
        playtime_2weeks: Playtime in the last two weeks in minutes.
        img_icon_url: Icon image hash (appended to Steam CDN URL).
        header_image: Full URL to the game's header image.
        last_played: Unix timestamp of the last play session.
    """

    app_id: int
    name: str
    playtime_forever: int = 0
    playtime_2weeks: int = 0
    img_icon_url: str = ""
    header_image: str = ""
    last_played: int = 0


@dataclass
class SteamChartsGame:
    """A game from Steam Charts most-played data.

    Attributes:
        app_id: Steam application identifier.
        name: Display name of the game (may be empty from chart data).
        current_players: Approximate concurrent player count.
    """

    app_id: int
    name: str = ""
    current_players: int = 0


@dataclass
class SteamPlayer:
    """Profile information for a Steam user.

    Attributes:
        steam_id: SteamID64 string.
        persona_name: Public display name.
        avatar_url: Full URL to the player's avatar image.
        profile_url: URL to the player's Steam community profile.
        last_logoff: Unix timestamp of the last logoff event.
    """

    steam_id: str
    persona_name: str
    avatar_url: str
    profile_url: str
    last_logoff: int = 0


@dataclass
class SteamOpenIdParams:
    """Validated parameters returned by the Steam OpenID callback.

    Attributes:
        steam_id: SteamID64 extracted from the claimed identity URL.
        params: Full set of OpenID query parameters for verification.
    """

    steam_id: str
    params: dict[str, str] = field(default_factory=dict)
