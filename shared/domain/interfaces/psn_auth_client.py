"""Interface for the PlayStation Network authentication and library client."""

from abc import ABC, abstractmethod

from modules.platforms.domain.entities.psn import PsnAuthToken, PsnGame


class IPsnAuthClient(ABC):
    """Contract for interacting with the PSN auth and user title APIs."""

    @abstractmethod
    async def exchange_npsso(self, npsso_code: str) -> PsnAuthToken:
        """Exchange an NPSSO cookie value for a PSN OAuth2 token pair.

        Args:
            npsso_code: NPSSO token extracted from the authenticated PSN session.
        """
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> PsnAuthToken:
        """Obtain a new token pair using a refresh token.

        Args:
            refresh_token: Long-lived refresh token from a previous auth.
        """
        ...

    @abstractmethod
    async def get_played_games(self, access_token: str) -> list[PsnGame]:
        """Fetch the list of played titles for the authenticated PSN user.

        Args:
            access_token: Valid PSN JWT bearer token.
        """
        ...

    @abstractmethod
    def build_login_url(self) -> str:
        """Build the PSN OAuth2 authorization URL.

        Returns:
            The full URL to redirect the user to for PSN login.
        """
        ...
