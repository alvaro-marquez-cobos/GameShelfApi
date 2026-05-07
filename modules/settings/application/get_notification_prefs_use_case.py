"""Use case: get user notification preferences."""

from typing import Any

from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from modules.settings.domain.interfaces.use_cases.get_notification_prefs import (
    IGetNotificationPrefsUseCase,
)

_DEFAULTS: dict[str, Any] = {"dealsEnabled": False}


class GetNotificationPrefsUseCase(IGetNotificationPrefsUseCase):
    """Retrieve notification preferences for a user."""

    def __init__(self, repo: ISettingsRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str) -> dict[str, Any]:
        prefs = await self._repo.get_notification_prefs(uid)
        return prefs if prefs is not None else _DEFAULTS
