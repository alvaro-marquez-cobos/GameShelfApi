"""Interface for the GOG authentication and library client."""

from abc import ABC, abstractmethod

from modules.platforms.domain.entities.gog import GogAuthToken, GogGame


class IGogAuthClient(ABC):
    """Contract for interacting with the GOG auth and library APIs."""

    @abstractmethod
    async def exchange_code(self, code: str) -> GogAuthToken:
        """Exchange an authorization code for a GOG OAuth2 token pair.

        Args:
            code: Short-lived authorization code from the GOG login callback.
        """
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> GogAuthToken:
        """Obtain a new token pair using a refresh token.

        Args:
            refresh_token: Long-lived refresh token from a previous auth.
        """
        ...

    @abstractmethod
    async def get_user_games(self, access_token: str) -> list[GogGame]:
        """Fetch the full game library for the authenticated GOG user.

        Args:
            access_token: Valid GOG bearer token.
        """
        ...

    @abstractmethod
    def build_auth_url(self) -> str:
        """Build the GOG OAuth2 authorization URL.

        Returns:
            The full URL to redirect the user to for GOG login.
        """
        ...
