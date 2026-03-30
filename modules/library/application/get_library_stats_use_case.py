"""Use case: compute aggregated statistics for the user's game library."""

from modules.library.domain.entities.library_stats import LibraryStats
from modules.library.domain.interfaces.repositories.i_library_repository import (
    ILibraryRepository,
)
from modules.library.domain.interfaces.use_cases.get_library_stats import (
    IGetLibraryStatsUseCase,
)
from shared.domain.enums.platform import Platform

_PC_PLATFORMS = {Platform.STEAM, Platform.EPIC, Platform.GOG}
_CONSOLE_PLATFORMS = {Platform.PSN}


class GetLibraryStatsUseCase(IGetLibraryStatsUseCase):
    """Compute totals and playtime aggregates from the user's library."""

    def __init__(self, repo: ILibraryRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str) -> LibraryStats:
        games = await self._repo.get_games(uid)

        pc_games = sum(1 for g in games if g.platform in _PC_PLATFORMS)
        console_games = sum(1 for g in games if g.platform in _CONSOLE_PLATFORMS)
        total_minutes = sum(g.playtime_minutes for g in games)

        return LibraryStats(
            total=len(games),
            pc_games=pc_games,
            console_games=console_games,
            total_playtime_hours=round(total_minutes / 60, 2),
        )
