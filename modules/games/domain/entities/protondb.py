"""ProtonDB compatibility rating entity."""

from dataclasses import dataclass

_VALID_TIERS: frozenset[str] = frozenset(
    {"platinum", "gold", "silver", "bronze", "borked", "pending"}
)


def to_proton_tier(value: str | None) -> str:
    """Return the tier string if valid, otherwise fall back to 'pending'."""
    if value and value in _VALID_TIERS:
        return value
    return "pending"


@dataclass(frozen=True)
class ProtonDbRating:
    """ProtonDB Linux/Proton compatibility rating for a Steam game.

    Args:
        tier: Overall compatibility tier (platinum, gold, silver, bronze, borked, pending).
        trending_tier: Trend-adjusted tier based on recent reports.
        total: Total number of reports submitted for this game.
    """

    tier: str
    trending_tier: str
    total: int
