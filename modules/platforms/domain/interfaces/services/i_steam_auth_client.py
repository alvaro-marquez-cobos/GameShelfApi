"""Interface for the Steam authentication and player API client."""

from abc import ABC, abstractmethod

from modules.platforms.domain.entities.steam import SteamChartsGame, SteamGame, SteamPlayer


class ISteamAuthClient(ABC):
    """Contract for interacting with the Steam Web API for auth and library data."""

    @abstractmethod
    async def get_owned_games(self, steam_id: str) -> list[SteamGame]:
        """Return the full list of games owned by the given Steam user."""
        ...

    @abstractmethod
    async def get_recently_played(self, steam_id: str) -> list[SteamGame]:
        """Return games played in the last two weeks for the given user."""
        ...

    @abstractmethod
    async def get_most_played_global(self, limit: int = 100) -> list[SteamChartsGame]:
        """Return the global most-played games chart."""
        ...

    @abstractmethod
    async def get_player_summary(self, steam_id: str) -> SteamPlayer | None:
        """Return profile information for the given Steam user."""
        ...

    @abstractmethod
    async def resolve_vanity_url(self, vanity: str) -> str | None:
        """Resolve a Steam vanity URL name to a SteamID64 string."""
        ...

    @abstractmethod
    def build_openid_url(self, return_url: str) -> str:
        """Build the Steam OpenID 2.0 authentication URL."""
        ...

    @abstractmethod
    async def verify_openid(self, params: dict[str, str]) -> str | None:
        """Verify an OpenID callback and extract the authenticated SteamID64."""
        ...
