"""Core user entity representing an authenticated user identity."""

from dataclasses import dataclass


@dataclass
class AuthenticatedUser:
    """Identity of a user extracted from a verified Firebase token.

    Attributes:
        uid: Firebase unique identifier.
        email: User email, None for anonymous accounts.
        display_name: User display name from the auth provider.
        photo_url: Avatar URL from the auth provider.
        is_guest: True if the user signed in anonymously.
        provider: Sign-in provider identifier (e.g. "google.com").
    """
    uid: str
    email: str | None
    display_name: str | None
    photo_url: str | None
    is_guest: bool
    provider: str
