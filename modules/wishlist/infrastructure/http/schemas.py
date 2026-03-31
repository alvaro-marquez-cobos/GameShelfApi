"""Pydantic schemas for wishlist HTTP endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from shared.domain.enums.platform import Platform


class WishlistItemResponse(BaseModel):
    """Wishlist item payload used by frontend."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    game_id: str = Field(alias="gameId")
    title: str
    platform: Platform
    cover_url: str | None = Field(default=None, alias="coverUrl")
    added_at: str = Field(alias="addedAt")
    best_deal_percentage: int | None = Field(default=None, alias="bestDealPercentage")


class GetWishlistResponse(BaseModel):
    """Wishlist response wrapper."""

    items: list[WishlistItemResponse]


class AddWishlistRequest(BaseModel):
    """Payload to add a game to wishlist."""

    model_config = ConfigDict(populate_by_name=True)

    game_id: str = Field(alias="gameId")
    title: str
    cover_url: str | None = Field(default=None, alias="coverUrl")
    steam_app_id: int | None = Field(default=None, alias="steamAppId")


class CheckWishlistResponse(BaseModel):
    """Boolean wishlist membership response."""

    model_config = ConfigDict(populate_by_name=True)

    is_in_wishlist: bool = Field(alias="isInWishlist")
