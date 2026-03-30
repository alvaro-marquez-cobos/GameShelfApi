"""Library module domain exceptions."""

from shared.exceptions import AppException, NotFoundException


class GameNotFoundException(NotFoundException):
    """Raised when a game is not found in the user's library."""

    def __init__(self, game_id: str) -> None:
        super().__init__(f"Game '{game_id}' not found in library")


class SyncFailedException(AppException):
    """Raised when a library sync fails for all platforms."""

    def __init__(self, message: str = "Library sync failed") -> None:
        super().__init__(500, "SYNC_FAILED", message)
