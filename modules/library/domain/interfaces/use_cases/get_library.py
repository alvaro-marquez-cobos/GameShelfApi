"""Interface for the get library use case."""

from abc import ABC, abstractmethod

from modules.library.domain.entities.library_game import LibraryGame
from modules.library.domain.enums.library import LibrarySortBy, LibraryTab


class IGetLibraryUseCase(ABC):
    """Contract for retrieving and filtering the user's game library."""

    @abstractmethod
    async def execute(
        self,
        uid: str,
        tab: LibraryTab = LibraryTab.ALL,
        sort_by: LibrarySortBy = LibrarySortBy.ALPHABETICAL,
        search: str = "",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[LibraryGame], int]:
        """Return a filtered/sorted page of games and the total count."""
        ...
