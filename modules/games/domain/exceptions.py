"""Games module domain exceptions."""

from shared.exceptions import NotFoundException


class GameNotFoundException(NotFoundException):
    """Raised when a requested game cannot be found."""

    def __init__(self, game_id: str) -> None:
        super().__init__(f"Game '{game_id}' not found")
