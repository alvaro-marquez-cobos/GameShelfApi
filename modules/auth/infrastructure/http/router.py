"""Auth module HTTP endpoints.

Provides routes for user sync (post-login), logout, account deletion,
and profile retrieval. All endpoints require a valid Firebase bearer token.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from composition.dependencies import (
    get_delete_account_use_case,
    get_get_profile_use_case,
    get_logout_use_case,
    get_sync_user_use_case,
)
from composition.security import get_current_user
from modules.auth.domain.interfaces.use_cases.delete_account import IDeleteAccountUseCase
from modules.auth.domain.interfaces.use_cases.get_profile import IGetProfileUseCase
from modules.auth.domain.interfaces.use_cases.logout import ILogoutUseCase
from modules.auth.domain.interfaces.use_cases.sync_user import ISyncUserUseCase
from modules.auth.infrastructure.http.schemas import MessageResponse, UserProfileResponse
from shared.domain.entities.user import AuthenticatedUser

router = APIRouter()


@router.post("/sync", response_model=UserProfileResponse)
async def sync_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ISyncUserUseCase, Depends(get_sync_user_use_case)],
) -> UserProfileResponse:
    data = await use_case.execute(current_user)
    return UserProfileResponse(**data)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ILogoutUseCase, Depends(get_logout_use_case)],
) -> MessageResponse:
    authorization = request.headers.get("Authorization", "")
    token = authorization.removeprefix("Bearer ").strip()
    await use_case.execute(token)
    return MessageResponse(message="Logged out successfully")


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IDeleteAccountUseCase, Depends(get_delete_account_use_case)],
) -> None:
    await use_case.execute(current_user.uid)


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetProfileUseCase, Depends(get_get_profile_use_case)],
) -> UserProfileResponse:
    data = await use_case.execute(current_user.uid)
    return UserProfileResponse(**data)
