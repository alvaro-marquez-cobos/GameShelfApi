"""Platforms module domain exceptions."""

from shared.exceptions import ConflictException, NotFoundException


class PlatformNotFoundException(NotFoundException):
    """Raised when a linked platform account does not exist."""

    def __init__(self, platform: str) -> None:
        super().__init__(f"Platform '{platform}' is not linked to this account")


class PlatformAlreadyLinkedException(ConflictException):
    """Raised when attempting to link a platform that is already linked."""

    def __init__(self, platform: str) -> None:
        super().__init__(f"Platform '{platform}' is already linked to this account")
