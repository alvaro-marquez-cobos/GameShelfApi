"""Game type identifiers."""

from enum import StrEnum


class GameType(StrEnum):
    """Type of game entry."""

    GAME = "game"
    DLC = "dlc"
