"""Domain entities for the home screen sections."""

from dataclasses import dataclass, field

from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.popular_game import PopularGame

__all__ = ["HomeData", "PopularGame"]


@dataclass
class HomeData:
    """Aggregated data for the home screen.

    Attributes:
        recently_played: Last played games from a content provider, or
            ``None`` if the provider is unavailable.
        most_played: Top games from the library by total playtime.
        popular_now: Globally trending games, or an empty list if the
            provider is unavailable.
    """

    recently_played: list[LibraryGame] | None = None
    most_played: list[LibraryGame] = field(default_factory=list)
    popular_now: list[PopularGame] = field(default_factory=list)
