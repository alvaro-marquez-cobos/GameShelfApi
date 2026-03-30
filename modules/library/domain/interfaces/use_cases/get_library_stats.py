"""Interface for the get library stats use case."""

from abc import ABC, abstractmethod

from modules.library.domain.entities.library_stats import LibraryStats


class IGetLibraryStatsUseCase(ABC):
    """Contract for computing aggregated library statistics."""

    @abstractmethod
    async def execute(self, uid: str) -> LibraryStats:
        """Return aggregated statistics for the user's library."""
        ...
