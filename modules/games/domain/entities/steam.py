"""Steam store domain entities for the games module."""

from dataclasses import dataclass, field


@dataclass
class SteamAppDetails:
    """Metadata for a Steam application fetched from the Steam Store API.

    Attributes:
        app_id: Steam application identifier.
        name: Display name of the application.
        short_description: Brief text description.
        header_image: URL to the horizontal banner image.
        genres: List of genre labels (e.g. "Action", "RPG").
        developers: Studio or developer names.
        publishers: Publisher names.
        release_date: Human-readable release date string, or None.
        metacritic_score: Metacritic score (0-100), or None.
        metacritic_url: URL to the Metacritic page, or None.
        screenshots: Full-resolution screenshot URLs.
        recommendation_count: Total Steam recommendation count, or None.
        app_type: Type string ("game", "dlc", "mod"), or None.
        parent_steam_app_id: App ID of the base game for DLC entries, or None.
        dlc_app_ids: App IDs of DLC packages for this title.
    """

    app_id: int
    name: str
    short_description: str = ""
    header_image: str = ""
    genres: list[str] = field(default_factory=list)
    developers: list[str] = field(default_factory=list)
    publishers: list[str] = field(default_factory=list)
    release_date: str | None = None
    metacritic_score: int | None = None
    metacritic_url: str | None = None
    screenshots: list[str] = field(default_factory=list)
    recommendation_count: int | None = None
    app_type: str | None = None
    parent_steam_app_id: int | None = None
    dlc_app_ids: list[int] = field(default_factory=list)
