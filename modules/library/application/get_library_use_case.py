"""Use case: retrieve and filter the user's game library."""

from collections import defaultdict

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

    @staticmethod
    def _merge_games(games: list[LibraryGame]) -> list[tuple[LibraryGame, list[Platform]]]:
        """Group multi-platform games by normalized title.

        Excludes DLCs (game_type == "DLC" or parent_game_id is not None),
        selects Steam as canonical when available, and accumulates platforms.
        """
        groups: dict[str, list[tuple[LibraryGame, Platform]]] = defaultdict(list)

        for game in games:
            if game.game_type == "DLC" or game.parent_game_id is not None:
                continue
            key = game.title.lower().strip()
            groups[key].append((game, game.platform))

        merged: list[tuple[LibraryGame, list[Platform]]] = []
        for _key, entries in groups.items():
            steam_entries = [e for e in entries if e[1] == Platform.STEAM]
            canonical = steam_entries[0][0] if steam_entries else entries[0][0]
            platforms = list(dict.fromkeys(p for _g, p in entries))
            merged.append((canonical, platforms))

        return merged

    async def execute(
        self,
        uid: str,
        tab: LibraryTab = LibraryTab.ALL,
        sort_by: LibrarySortBy = LibrarySortBy.ALPHABETICAL,
        search: str = "",
        offset: int = 0,
        limit: int = 20,
        platforms: list[Platform] | None = None,
    ) -> tuple[list[LibraryGame], int, list[list[Platform]]]:
        games = await self._repo.get_games(uid)

        if tab == LibraryTab.PC:
            games = [g for g in games if g.platform in _PC_PLATFORMS]
        elif tab == LibraryTab.CONSOLE:
            games = [g for g in games if g.platform in _CONSOLE_PLATFORMS]

        if platforms is not None and len(platforms) > 0:
            games = [g for g in games if g.platform in platforms]

        if search:
            search_lower = search.lower()
            games = [g for g in games if search_lower in g.title.lower()]

        merged = self._merge_games(games)

        if sort_by == LibrarySortBy.ALPHABETICAL:
            merged.sort(key=lambda g_plat: g_plat[0].title.lower())
        elif sort_by == LibrarySortBy.LAST_PLAYED:
            merged.sort(
                key=lambda g_plat: g_plat[0].last_played or "",
                reverse=True,
            )
        elif sort_by == LibrarySortBy.PLAYTIME:
            merged.sort(key=lambda g_plat: g_plat[0].playtime_minutes, reverse=True)

        total = len(merged)
        page_items = merged[offset : offset + limit]

        return [item for item, _ in page_items], total, [item[1] for item in page_items]
