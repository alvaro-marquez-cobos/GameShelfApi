"""Interface for the search games use case."""

from abc import ABC, abstractmethod

from modules.search.domain.entities.search_result import SearchResult


class ISearchGamesUseCase(ABC):
    """Contract for searching games with user-specific ownership flags."""

    @abstractmethod
    async def execute(self, uid: str, query: str) -> list[SearchResult]:
        """Search for games matching *query* and annotate with user context.

        Args:
            uid: Firebase UID of the requesting user.
            query: Search term.

        Returns:
            Up to 20 results with ``is_owned`` and ``is_in_wishlist`` flags.
        """
        ...
