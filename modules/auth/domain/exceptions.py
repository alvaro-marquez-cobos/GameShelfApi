"""Auth module domain exceptions.

These exceptions represent error conditions specific to authentication
and user account operations.
"""

from shared.exceptions import AppException, NotFoundException, UnauthorizedException


class InvalidTokenException(UnauthorizedException):
    """Raised when a provided token cannot be decoded or verified."""

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)


class TokenBlacklistedException(UnauthorizedException):
    """Raised when a token has already been revoked via logout."""

    def __init__(self, message: str = "Token has been revoked") -> None:
        super().__init__(message)


class UserNotFoundException(NotFoundException):
    """Raised when a user profile does not exist in the database."""

    def __init__(self, uid: str) -> None:
        super().__init__(f"User {uid} not found")


class AccountDeletionException(AppException):
    """Raised when the account deletion process fails at any step."""

    def __init__(self, message: str = "Failed to delete account") -> None:
        super().__init__(500, "ACCOUNT_DELETION_ERROR", message)
