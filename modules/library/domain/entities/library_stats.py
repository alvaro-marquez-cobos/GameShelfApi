"""Domain entity for aggregated user library statistics."""

from dataclasses import dataclass


@dataclass
class LibraryStats:
    """Aggregated statistics about a user's game library.

    Attributes:
        total: Total number of games across all platforms.
        pc_games: Games on PC platforms (Steam, Epic, GOG).
        console_games: Games on console platforms (PSN).
        total_playtime_hours: Sum of all playtime converted to hours.
    """

    total: int
    pc_games: int
    console_games: int
    total_playtime_hours: float
