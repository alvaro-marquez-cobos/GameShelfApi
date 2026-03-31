"""Enums for library filtering and sorting."""

from enum import StrEnum


class LibraryTab(StrEnum):
    """Tab filter for the user game library."""

    ALL = "all"
    PC = "pc"
    CONSOLE = "console"


class LibrarySortBy(StrEnum):
    """Sort criteria for the user game library."""

    ALPHABETICAL = "alphabetical"
    LAST_PLAYED = "last_played"
    PLAYTIME = "playtime"
