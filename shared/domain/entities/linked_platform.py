"""Domain entity representing a linked external platform account."""

from dataclasses import dataclass

from shared.domain.enums.platform import Platform


@dataclass
class LinkedPlatform:
    """An external gaming platform account linked to the user.

    Attributes:
        platform: The platform identifier (Steam, Epic, GOG, PSN).
        username: The display name or username on that platform.
        avatar_url: Avatar image URL from the platform, or None.
        linked_at: ISO-8601 timestamp of when the account was linked.
    """

    platform: Platform
    username: str
    avatar_url: str | None = None
    linked_at: str = ""
