"""Authentication provider identifiers."""

from enum import StrEnum


class AuthProvider(StrEnum):
    """Supported Firebase sign-in providers."""

    GOOGLE = "google.com"
    ANONYMOUS = "anonymous"
