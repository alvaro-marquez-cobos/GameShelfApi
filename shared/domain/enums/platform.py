"""Supported gaming platform identifiers."""

from enum import StrEnum


class Platform(StrEnum):
    """Gaming platforms supported by GameShelf."""

    STEAM = "steam"
    EPIC = "epic_games"
    GOG = "gog"
    PSN = "psn"

    @classmethod
    def from_raw(cls, raw: object) -> "Platform":
        """Parse a platform value from canonical or legacy representations."""
        if isinstance(raw, Platform):
            return raw

        value = str(raw).strip().lower()
        aliases: dict[str, Platform] = {
            "steam": cls.STEAM,
            "epic": cls.EPIC,
            "epic_games": cls.EPIC,
            "gog": cls.GOG,
            "psn": cls.PSN,
        }
        if value not in aliases:
            raise ValueError(f"Unknown platform: {raw}")
        return aliases[value]
