"""Game detail and DLC detail entities for the games module."""

from dataclasses import dataclass, field

from modules.games.domain.entities.hltb import HltbResult
from modules.games.domain.entities.itad import Deal
from modules.games.domain.entities.protondb import ProtonDbRating
from modules.games.domain.entities.steam import SteamAppDetails
from shared.domain.enums.platform import Platform


@dataclass
class GameDetail:
    """Fully enriched game detail aggregating data from all external services.

    Attributes:
        game_id: Deterministic library ID (e.g. ``steam_570``).
        title: Display title of the game.
        steam_app_id: Resolved Steam app ID, or None if unavailable.
        platform: Platform the game belongs to.
        cover_url: Horizontal cover image URL from the user's library, or None.
        portrait_cover_url: Portrait cover image URL (Steam 600x900), or None.
        playtime_minutes: Total playtime in minutes from the user's library.
        last_played: ISO-8601 timestamp of the last play session, or None.
        description: Short description sourced from Steam metadata, or empty.
        steam: Steam Store metadata, or None if enrichment failed.
        protondb: ProtonDB Linux compatibility rating, or None.
        hltb: HowLongToBeat completion times, or None.
        deals: Current ITAD store deals (empty if unavailable).
        is_in_wishlist: Whether the game is on the user's wishlist.
    """

    game_id: str
    title: str
    steam_app_id: int | None
    platform: Platform = Platform.STEAM
    cover_url: str | None = None
    portrait_cover_url: str | None = None
    playtime_minutes: int = 0
    last_played: str | None = None
    description: str = ""
    steam: SteamAppDetails | None = None
    protondb: ProtonDbRating | None = None
    hltb: HltbResult | None = None
    deals: list[Deal] = field(default_factory=list)
    is_in_wishlist: bool = False
    is_in_library: bool = False


@dataclass
class DlcDetail:
    """Summary of a single DLC entry returned by GetGameDlcsUseCase.

    Attributes:
        app_id: Steam app ID of the DLC.
        name: Display name of the DLC.
        header_image: URL to the DLC header image.
        is_owned: Whether the user owns this DLC in their library.
    """

    app_id: int
    name: str
    header_image: str
    is_owned: bool
