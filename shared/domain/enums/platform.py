"""Supported gaming platform identifiers."""

from enum import StrEnum


class Platform(StrEnum):
    """Gaming platforms supported by GameShelf."""

    STEAM = "steam"
    EPIC = "epic"
    GOG = "gog"
    PSN = "psn"
