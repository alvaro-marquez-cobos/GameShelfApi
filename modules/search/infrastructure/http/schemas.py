"""Pydantic schemas for search HTTP endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from shared.domain.enums.platform import Platform


class SearchResultResponse(BaseModel):
    """Single search result row."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    cover_url: str = Field(alias="coverUrl")
    steam_app_id: int | None = Field(default=None, alias="steamAppId")
    game_type: str | None = Field(default=None, alias="gameType")
    is_owned: bool = Field(alias="isOwned")
    owned_platforms: list[Platform] = Field(default_factory=list, alias="ownedPlatforms")
    is_in_wishlist: bool = Field(alias="isInWishlist")


class SearchResponse(BaseModel):
    """Search response wrapper."""

    results: list[SearchResultResponse]
