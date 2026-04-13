"""Get home screen data use case."""

import asyncio
import logging

from modules.home.domain.entities.home_data import HomeData
from modules.home.domain.interfaces.use_cases.get_home import IGetHomeUseCase
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.popular_game import PopularGame
from shared.domain.interfaces.i_home_content_provider import IHomeContentProvider
from shared.domain.interfaces.i_library_reader import ILibraryReader

logger = logging.getLogger(__name__)

_MOST_PLAYED_LIMIT = 5
_POPULAR_LIMIT = 20


class GetHomeUseCase(IGetHomeUseCase):
    """Assemble home screen data from a content provider and the user's library."""

    def __init__(
        self,
        content_provider: IHomeContentProvider,
        library_reader: ILibraryReader,
    ) -> None:
        self._provider = content_provider
        self._library = library_reader

    async def execute(self, uid: str) -> HomeData:
        results = await asyncio.gather(
            self._provider.get_recently_played(uid),
            self._library.get_most_played(uid, _MOST_PLAYED_LIMIT),
            self._provider.get_globally_popular(_POPULAR_LIMIT),
            return_exceptions=True,
        )

        recently_played_raw = results[0]
        recently_played: list[LibraryGame] | None
        if isinstance(recently_played_raw, BaseException):
            logger.warning("Failed to fetch recently played: %s", recently_played_raw)
            recently_played = None
        else:
            recently_played = recently_played_raw

        most_played_raw = results[1]
        most_played: list[LibraryGame]
        if isinstance(most_played_raw, BaseException):
            logger.warning("Failed to fetch most played: %s", most_played_raw)
            most_played = []
        else:
            most_played = list(most_played_raw)

        popular_raw = results[2]
        popular_now: list[PopularGame]
        if isinstance(popular_raw, BaseException):
            logger.warning("Failed to fetch global popular games: %s", popular_raw)
            popular_now = []
        else:
            popular_now = list(popular_raw)

        return HomeData(
            recently_played=recently_played,
            most_played=most_played,
            popular_now=popular_now,
        )
