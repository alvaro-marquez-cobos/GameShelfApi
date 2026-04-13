"""Shared DTO for globally popular games."""

from dataclasses import dataclass


@dataclass
class PopularGame:
    """A globally popular game.

    Attributes:
        steam_app_id: Steam App ID, if sourced from Steam.
        title: Game title.
        current_players: Approximate concurrent player count.
        cover_url: Cover image URL, or None.
    """

    steam_app_id: int
    title: str
    current_players: int
    cover_url: str | None = None
