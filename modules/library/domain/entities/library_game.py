"""Domain entity representing a game in a user's library.

LibraryGame is defined in shared so it can be used across modules
without creating direct inter-module dependencies.
"""

from shared.domain.entities.library_game import LibraryGame

__all__ = ["LibraryGame"]
