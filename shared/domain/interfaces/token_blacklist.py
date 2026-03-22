"""Interface for token blacklisting to support logout and revocation."""

from abc import ABC, abstractmethod


class ITokenBlacklist(ABC):
    """Contract for tracking revoked tokens until they naturally expire."""
    @abstractmethod
    async def add(self, token_id: str, ttl_seconds: int) -> None:
        """Blacklist a token for the given duration.

        Args:
            token_id: Unique identifier of the token (JTI or uid:iat).
            ttl_seconds: Time in seconds until the entry auto-expires.
        """
        ...

    @abstractmethod
    async def is_blacklisted(self, token_id: str) -> bool:
        """Check whether a token has been revoked."""
        ...
