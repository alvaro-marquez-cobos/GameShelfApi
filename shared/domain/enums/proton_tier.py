"""ProtonDB compatibility rating tiers."""

from enum import StrEnum


class ProtonTier(StrEnum):
    """ProtonDB compatibility levels for Linux gaming."""

    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    BORKED = "borked"
    PENDING = "pending"
