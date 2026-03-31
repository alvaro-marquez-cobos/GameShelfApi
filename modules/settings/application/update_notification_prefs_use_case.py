"""Use case: update user notification preferences."""

from typing import Any

from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from modules.settings.domain.interfaces.use_cases.update_notification_prefs import (
    IUpdateNotificationPrefsUseCase,
)


class UpdateNotificationPrefsUseCase(IUpdateNotificationPrefsUseCase):
    """Update notification preferences for a user."""

    def __init__(self, repo: ISettingsRepository) -> None:
        self._repo = repo

    async def execute(self, uid: str, prefs: dict[str, Any]) -> None:
        await self._repo.update_notification_prefs(uid, prefs)
