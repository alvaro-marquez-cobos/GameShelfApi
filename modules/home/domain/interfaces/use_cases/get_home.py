"""Interface for the get home use case."""

from abc import ABC, abstractmethod

from modules.home.domain.entities.home_data import HomeData


class IGetHomeUseCase(ABC):
    """Contract for assembling home screen data."""

    @abstractmethod
    async def execute(self, uid: str) -> HomeData:
        """Return aggregated home screen sections for the user.

        Sections unavailable due to service failures are set to None.
        """
        ...
