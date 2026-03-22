"""Interface for the Epic Games authentication and library client."""

from abc import ABC, abstractmethod

from modules.platforms.domain.entities.epic import EpicAuthToken, EpicCatalogItem, EpicGame


class IEpicAuthClient(ABC):
    """Contract for interacting with the Epic Games auth and library APIs."""

    @abstractmethod
    async def exchange_auth_code(self, code: str) -> EpicAuthToken:
        """Exchange an authorization code for an Epic OAuth2 token pair.

        Args:
            code: Short-lived authorization code from the Epic login callback.
        """
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> EpicAuthToken:
        """Obtain a new token pair using a refresh token.

        Args:
            refresh_token: Long-lived refresh token from a previous auth.
        """
        ...

    @abstractmethod
    async def fetch_library(self, access_token: str, account_id: str) -> list[EpicGame]:
        """Fetch the full game library for an Epic account.

        Args:
            access_token: Valid Epic bearer token.
            account_id: Epic account identifier of the user.
        """
        ...

    @abstractmethod
    async def enrich_catalog_items(
        self,
        namespace: str,
        item_ids: list[str],
        access_token: str,
    ) -> list[EpicCatalogItem]:
        """Fetch enriched catalog metadata for a batch of Epic items.

        Args:
            namespace: Epic catalog namespace.
            item_ids: List of catalog item IDs (max 50 per call).
            access_token: Valid Epic bearer token.
        """
        ...

    @abstractmethod
    def parse_gdpr_export(self, json_content: str) -> list[EpicGame]:
        """Parse an Epic GDPR data export JSON payload into game entries.

        Args:
            json_content: Raw JSON string from the GDPR export file.
        """
        ...

    @abstractmethod
    def build_login_url(self) -> str:
        """Build the Epic Games OAuth2 authorization URL.

        Returns:
            The full URL to redirect the user to for Epic login.
        """
        ...
