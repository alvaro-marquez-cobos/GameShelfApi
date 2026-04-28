"""Settings module HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition.dependencies import (
    get_get_notification_prefs_use_case,
    get_settings_repository,
    get_update_notification_prefs_use_case,
)
from composition.security import get_current_user
from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from modules.settings.domain.interfaces.use_cases.get_notification_prefs import (
    IGetNotificationPrefsUseCase,
)
from modules.settings.domain.interfaces.use_cases.update_notification_prefs import (
    IUpdateNotificationPrefsUseCase,
)
from modules.settings.infrastructure.http.schemas import (
    CountryResponse,
    NotificationPrefsResponse,
    UpdateCountryRequest,
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


@router.get("/country", response_model=CountryResponse)
async def get_country(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[ISettingsRepository, Depends(get_settings_repository)],
) -> CountryResponse:
    country_code = await repo.get_itad_country(current_user.uid)
    return CountryResponse(country_code=country_code)


@router.put("/country", status_code=status.HTTP_204_NO_CONTENT)
async def update_country(
    body: UpdateCountryRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[ISettingsRepository, Depends(get_settings_repository)],
) -> None:
    await repo.update_itad_country(current_user.uid, body.country_code)
