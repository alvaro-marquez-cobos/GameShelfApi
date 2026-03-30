"""Interface for the sync library use case."""

from abc import ABC, abstractmethod

from shared.domain.enums.platform import Platform


class ISyncLibraryUseCase(ABC):
    """Contract for syncing the user's game library from external platforms."""

    @abstractmethod
    async def execute(self, uid: str, platform: Platform | None = None) -> int:
        """Sync games from all linked platforms (or a specific one).

        Returns:
            Total number of games synced.
        """
        ...
