"""Pydantic schemas for library HTTP endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from modules.library.domain.enums.library import LibrarySortBy, LibraryTab
from shared.domain.enums.platform import Platform


class LibraryGameResponse(BaseModel):
    """A game entry returned by library/home endpoints."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="gameId")
    title: str
    platform: Platform
    cover_url: str | None = Field(default=None, alias="coverUrl")
    playtime_minutes: int = Field(default=0, alias="playtimeMinutes")
    last_played: str | None = Field(default=None, alias="lastPlayed")
    steam_app_id: int | None = Field(default=None, alias="steamAppId")


class GetLibraryResponse(BaseModel):
    """Paginated library response."""

    model_config = ConfigDict(populate_by_name=True)

    games: list[LibraryGameResponse]
    total: int
    has_more: bool = Field(alias="hasMore")


class LibraryStatsResponse(BaseModel):
    """Aggregated library statistics response."""

    model_config = ConfigDict(populate_by_name=True)

    total_games: int = Field(alias="totalGames")
    pc_games: int = Field(alias="pcGames")
    console_games: int = Field(alias="consoleGames")
    total_playtime: float = Field(alias="totalPlaytime")


class SyncLibraryRequest(BaseModel):
    """Optional platform filter for sync."""

    platform: Platform | None = None


class SyncLibraryResponse(BaseModel):
    """Number of synchronized games."""

    synced: int


class GetLibraryQuery(BaseModel):
    """Query parameters accepted by GET /library."""

    tab: LibraryTab = LibraryTab.ALL
    sort: LibrarySortBy = LibrarySortBy.ALPHABETICAL
    search: str = ""
    page: int = 1
    page_size: int = 200
