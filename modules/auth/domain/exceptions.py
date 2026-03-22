from shared.exceptions import AppException, NotFoundException, UnauthorizedException


class InvalidTokenException(UnauthorizedException):
    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)


class TokenBlacklistedException(UnauthorizedException):
    def __init__(self, message: str = "Token has been revoked") -> None:
        super().__init__(message)


class UserNotFoundException(NotFoundException):
    def __init__(self, uid: str) -> None:
        super().__init__(f"User {uid} not found")


class AccountDeletionException(AppException):
    def __init__(self, message: str = "Failed to delete account") -> None:
        super().__init__(500, "ACCOUNT_DELETION_ERROR", message)
