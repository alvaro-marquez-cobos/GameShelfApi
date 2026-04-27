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
        total_unique: Number of unique games after cross-platform deduplication.
        pc_unique: Number of unique games on PC platforms after deduplication.
        console_unique: Number of unique games on console platforms after deduplication.
    """

    total: int
    pc_games: int
    console_games: int
    total_playtime_hours: float
    total_unique: int = 0
    pc_unique: int = 0
    console_unique: int = 0
