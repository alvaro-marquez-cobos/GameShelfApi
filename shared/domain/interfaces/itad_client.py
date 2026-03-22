"""Interface for the IsThereAnyDeal client."""

from abc import ABC, abstractmethod

from modules.games.domain.entities.itad import Deal, ItadGameInfo, ItadSearchResult


class IItadClient(ABC):
    """Contract for IsThereAnyDeal price and game lookup operations."""

    @abstractmethod
    async def lookup_game_id(self, title: str) -> str | None:
        """Resolve a game title to an ITAD UUID.

        Args:
            title: Game title to resolve.

        Returns:
            ITAD UUID string, or None if not found.
        """
        ...

    @abstractmethod
    async def lookup_game_ids_batch(self, titles: list[str]) -> dict[str, str | None]:
        """Resolve multiple game titles to ITAD UUIDs in a single request.

        Args:
            titles: List of game titles to resolve.

        Returns:
            Mapping of title → ITAD UUID (None if not found).
        """
        ...

    @abstractmethod
    async def lookup_game_id_by_steam_app_id(self, steam_app_id: str) -> str | None:
        """Resolve a Steam app ID to an ITAD UUID.

        Args:
            steam_app_id: Numeric Steam app ID as a string.

        Returns:
            ITAD UUID string, or None if not found.
        """
        ...

    @abstractmethod
    async def get_prices_for_game(self, itad_game_id: str, country: str = "US") -> list[Deal]:
        """Fetch current store deals for a game.

        Args:
            itad_game_id: ITAD UUID of the game.
            country: ISO 3166-1 alpha-2 country code for pricing.

        Returns:
            List of current deals sorted by ITAD's default ordering.
        """
        ...

    @abstractmethod
    async def get_prices_for_games_batch(
        self, itad_game_ids: list[str], country: str = "US"
    ) -> dict[str, list[Deal]]:
        """Fetch current deals for multiple games in a single request.

        Args:
            itad_game_ids: List of ITAD UUIDs.
            country: ISO 3166-1 alpha-2 country code for pricing.

        Returns:
            Mapping of ITAD UUID → list of deals.
        """
        ...

    @abstractmethod
    async def get_historical_low(self, itad_game_id: str, country: str = "US") -> Deal | None:
        """Fetch the all-time historical low price for a game.

        Args:
            itad_game_id: ITAD UUID of the game.
            country: ISO 3166-1 alpha-2 country code for pricing.

        Returns:
            A ``Deal`` representing the historical low, or None if unavailable.
        """
        ...

    @abstractmethod
    async def search_games(self, query: str) -> list[ItadSearchResult]:
        """Search for games by title on ITAD.

        The first 5 results are enriched with Steam app IDs when available.

        Args:
            query: Search term.

        Returns:
            List of up to 20 search results.
        """
        ...

    @abstractmethod
    async def get_game_info(self, itad_game_id: str) -> ItadGameInfo | None:
        """Fetch metadata for a game from ITAD.

        Args:
            itad_game_id: ITAD UUID of the game.

        Returns:
            An ``ItadGameInfo`` instance, or None if not found.
        """
        ...
