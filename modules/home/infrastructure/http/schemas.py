"""Pydantic schemas for home HTTP endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from modules.library.infrastructure.http.schemas import LibraryGameResponse


class PopularGameResponse(BaseModel):
    """Popular global game response item."""

    model_config = ConfigDict(populate_by_name=True)

    game_id: str = Field(alias="gameId")
    steam_app_id: int = Field(alias="steamAppId")
    title: str
    current_players: int = Field(alias="currentPlayers")
    cover_url: str | None = Field(default=None, alias="coverUrl")


class HomeResponse(BaseModel):
    """Aggregated home sections response."""

    model_config = ConfigDict(populate_by_name=True)

    recently_played: list[LibraryGameResponse] | None = Field(default=None, alias="recentlyPlayed")
    most_played: list[LibraryGameResponse] = Field(alias="mostPlayed")
    popular_now: list[PopularGameResponse] = Field(default_factory=list, alias="popularNow")


class PopularOnlyResponse(BaseModel):
    """Popular section response wrapper."""

    games: list[PopularGameResponse]
