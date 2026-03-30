"""Domain entity representing a game in a user's library."""

from dataclasses import dataclass, field

from shared.domain.enums.platform import Platform


@dataclass
class LibraryGame:
    """A game entry in the user's cross-platform library.

    Attributes:
        game_id: Deterministic ID in the form ``{platform}_{external_id}``
            (e.g. ``steam_570``, ``epic_fortnite``).
        title: Display title of the game.
        platform: Platform the game belongs to.
        cover_url: URL of the cover/box art image, or None if unavailable.
        playtime_minutes: Total playtime recorded in minutes.
        last_played: ISO-8601 timestamp of the last play session, or None.
        steam_app_id: Steam App ID used for metadata enrichment, or None if
            this game is not on Steam or the ID has not been resolved yet.
        extra: Platform-specific fields that do not have a canonical place
            (e.g. Epic namespace, GOG product ID).
    """

    game_id: str
    title: str
    platform: Platform
    cover_url: str | None = None
    playtime_minutes: int = 0
    last_played: str | None = None
    steam_app_id: int | None = None
    extra: dict[str, object] = field(default_factory=dict)
