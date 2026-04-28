"""Pydantic schemas for games HTTP endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from shared.domain.enums.platform import Platform


class GameSummaryResponse(BaseModel):
    """Game summary embedded in game detail responses."""

    model_config = ConfigDict(populate_by_name=True)

    game_id: str = Field(alias="gameId")
    title: str
    platform: Platform = Platform.STEAM
    steam_app_id: int | None = Field(default=None, alias="steamAppId")
    cover_url: str | None = Field(default=None, alias="coverUrl")
    portrait_cover_url: str | None = Field(default=None, alias="portraitCoverUrl")
    playtime_minutes: int = Field(default=0, alias="playtime")
    last_played: str | None = Field(default=None, alias="lastPlayed")
    description: str = ""


class ProtonDbResponse(BaseModel):
    """ProtonDB compatibility payload."""

    tier: str
    trending_tier: str = Field(alias="trendingTier")
    total_reports: int = Field(alias="totalReports")


class HowLongToBeatResponse(BaseModel):
    """HowLongToBeat durations in hours."""

    main_hours: float | None = Field(alias="mainHours")
    main_extra_hours: float | None = Field(alias="mainExtraHours")
    completionist_hours: float | None = Field(alias="completionistHours")


class SteamMetadataResponse(BaseModel):
    """Steam metadata subset used by the frontend."""

    genres: list[str]
    developers: list[str]
    publishers: list[str]
    release_date: str | None = Field(alias="releaseDate")
    metacritic_score: int | None = Field(alias="metacriticScore")
    recommendation_count: int | None = Field(alias="recommendationCount")
    screenshots: list[str]


class DealResponse(BaseModel):
    """Store deal entry."""

    id: str
    store_name: str = Field(alias="storeName")
    price: float
    original_price: float = Field(alias="originalPrice")
    discount_percentage: int = Field(alias="discountPercentage")
    url: str
    currency: str


class GameDetailResponse(BaseModel):
    """Aggregated game detail response."""

    model_config = ConfigDict(populate_by_name=True)

    game: GameSummaryResponse
    proton_db: ProtonDbResponse | None = Field(default=None, alias="protonDb")
    how_long_to_beat: HowLongToBeatResponse | None = Field(default=None, alias="howLongToBeat")
    steam_metadata: SteamMetadataResponse | None = Field(default=None, alias="steamMetadata")
    deals: list[DealResponse]
    is_in_wishlist: bool = Field(alias="isInWishlist")
    is_in_library: bool = Field(alias="isInLibrary")


class DlcResponse(BaseModel):
    """Single DLC item response."""

    app_id: int = Field(alias="appId")
    name: str
    header_image: str = Field(alias="headerImage")
    is_owned: bool = Field(alias="isOwned")


class GetGameDlcsResponse(BaseModel):
    """DLC list response wrapper."""

    model_config = ConfigDict(populate_by_name=True)

    dlcs: list[DlcResponse]
