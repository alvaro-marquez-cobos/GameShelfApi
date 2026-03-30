"""Use case: retrieve and filter the user's game library."""

from modules.library.domain.entities.library_game import LibraryGame
from modules.library.domain.enums.library import LibrarySortBy, LibraryTab
from modules.library.domain.interfaces.repositories.i_library_repository import (
    ILibraryRepository,
)
from modules.library.domain.interfaces.use_cases.get_library import IGetLibraryUseCase
from shared.domain.enums.platform import Platform

_PC_PLATFORMS = {Platform.STEAM, Platform.EPIC, Platform.GOG}
_CONSOLE_PLATFORMS = {Platform.PSN}


class GetLibraryUseCase(IGetLibraryUseCase):
    """Return a paginated, filtered, and sorted view of the user's library."""

    def __init__(self, repo: ILibraryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        uid: str,
        tab: LibraryTab = LibraryTab.ALL,
        sort_by: LibrarySortBy = LibrarySortBy.ALPHABETICAL,
        search: str = "",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[LibraryGame], int]:
        games = await self._repo.get_games(uid)

        if tab == LibraryTab.PC:
            games = [g for g in games if g.platform in _PC_PLATFORMS]
        elif tab == LibraryTab.CONSOLE:
            games = [g for g in games if g.platform in _CONSOLE_PLATFORMS]

        if search:
            search_lower = search.lower()
            games = [g for g in games if search_lower in g.title.lower()]

        total = len(games)

        if sort_by == LibrarySortBy.ALPHABETICAL:
            games.sort(key=lambda g: g.title.lower())
        elif sort_by == LibrarySortBy.LAST_PLAYED:
            games.sort(key=lambda g: g.last_played or "", reverse=True)
        elif sort_by == LibrarySortBy.PLAYTIME:
            games.sort(key=lambda g: g.playtime_minutes, reverse=True)

        return games[offset : offset + limit], total
