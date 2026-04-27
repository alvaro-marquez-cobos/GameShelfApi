"""Use case: compute aggregated statistics for the user's game library."""

from modules.library.domain.entities.library_stats import LibraryStats
from modules.library.domain.interfaces.repositories.i_library_repository import (
    ILibraryRepository,
)
from modules.library.domain.interfaces.use_cases.get_library_stats import (
    IGetLibraryStatsUseCase,
)
from shared.domain.entities.library_game import LibraryGame
from shared.domain.enums.platform import Platform

_PC_PLATFORMS = {Platform.STEAM, Platform.EPIC, Platform.GOG}
_CONSOLE_PLATFORMS = {Platform.PSN}
_PLATFORM_PREFERENCE = [Platform.STEAM, Platform.EPIC, Platform.GOG, Platform.PSN]


class GetLibraryStatsUseCase(IGetLibraryStatsUseCase):
    """Compute totals and playtime aggregates from the user's library."""

    def __init__(self, repo: ILibraryRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str) -> LibraryStats:
        games = await self._repo.get_games(uid)

        total_minutes = sum(g.playtime_minutes for g in games)

        pc_games = sum(1 for g in games if g.platform in _PC_PLATFORMS)
        console_games = sum(1 for g in games if g.platform in _CONSOLE_PLATFORMS)

        deduped = _dedup_games(games)

        total_unique = len(deduped)
        pc_unique = sum(1 for g in deduped if g.platform in _PC_PLATFORMS)
        console_unique = sum(1 for g in deduped if g.platform in _CONSOLE_PLATFORMS)

        return LibraryStats(
            total=len(games),
            pc_games=pc_games,
            console_games=console_games,
            total_playtime_hours=round(total_minutes / 60, 2),
            total_unique=total_unique,
            pc_unique=pc_unique,
            console_unique=console_unique,
        )


def _dedup_games(games: list[LibraryGame]) -> list[LibraryGame]:
    """Deduplicate games by normalized title, preferring higher-priority platforms."""
    canonical_order = {platform: idx for idx, platform in enumerate(_PLATFORM_PREFERENCE)}
    map: dict[str, LibraryGame] = {}
    for game in games:
        title = game.title.lower().strip()
        existing = map.get(title)
        if existing is None:
            map[title] = game
        else:
            existing_idx = canonical_order.get(existing.platform, 999)
            new_idx = canonical_order.get(game.platform, 999)
            if new_idx < existing_idx:
                map[title] = game
    return list(map.values())
