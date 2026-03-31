"""Settings module HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition.dependencies import (
    get_get_notification_prefs_use_case,
    get_update_notification_prefs_use_case,
)
from composition.security import get_current_user
from modules.settings.domain.interfaces.use_cases.get_notification_prefs import (
    IGetNotificationPrefsUseCase,
)
from modules.settings.domain.interfaces.use_cases.update_notification_prefs import (
    IUpdateNotificationPrefsUseCase,
)
from modules.settings.infrastructure.http.schemas import (
    NotificationPrefsResponse,
    UpdateNotificationPrefsRequest,
)
from shared.domain.entities.user import AuthenticatedUser

router = APIRouter()


@router.get("/notifications", response_model=NotificationPrefsResponse)
async def get_notification_prefs(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[
        IGetNotificationPrefsUseCase,
        Depends(get_get_notification_prefs_use_case),
    ],
) -> NotificationPrefsResponse:
    prefs = await use_case.execute(current_user.uid)
    return NotificationPrefsResponse(deals_enabled=bool(prefs.get("dealsEnabled", False)))


@router.put("/notifications", status_code=status.HTTP_204_NO_CONTENT)
async def update_notification_prefs(
    body: UpdateNotificationPrefsRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[
        IUpdateNotificationPrefsUseCase,
        Depends(get_update_notification_prefs_use_case),
    ],
) -> None:
    await use_case.execute(current_user.uid, {"dealsEnabled": body.deals_enabled})
