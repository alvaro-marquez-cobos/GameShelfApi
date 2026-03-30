"""Domain entities for the home screen sections."""

from dataclasses import dataclass, field

from modules.library.domain.entities.library_game import LibraryGame


@dataclass
class PopularGame:
    """A globally popular game sourced from Steam Charts.

    Attributes:
        steam_app_id: Steam App ID.
        title: Game title.
        current_players: Approximate concurrent player count.
        cover_url: Cover image URL, or None.
    """

    steam_app_id: int
    title: str
    current_players: int
    cover_url: str | None = None


@dataclass
class HomeData:
    """Aggregated data for the home screen.

    Attributes:
        recently_played: Last played games from Steam, or None if Steam
            is not linked or the request fails.
        most_played: Top 5 games from the library by total playtime.
        popular_now: Globally trending games from Steam Charts, or None
            if the request fails.
    """

    recently_played: list[LibraryGame] | None = None
    most_played: list[LibraryGame] = field(default_factory=list)
    popular_now: list[PopularGame] | None = None
