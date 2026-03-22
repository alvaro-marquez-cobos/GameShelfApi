from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from composition.security import get_current_user
from modules.auth.application.delete_account_use_case import DeleteAccountUseCase
from modules.auth.application.get_profile_use_case import GetProfileUseCase
from modules.auth.application.logout_use_case import LogoutUseCase
from modules.auth.application.sync_user_use_case import SyncUserUseCase
from modules.auth.infrastructure.http.schemas import MessageResponse, UserProfileResponse
from shared.domain.entities.user import AuthenticatedUser

router = APIRouter()


def _get_sync_use_case() -> SyncUserUseCase:
    from composition.dependencies import get_user_repository

    return SyncUserUseCase(get_user_repository())


def _get_logout_use_case() -> LogoutUseCase:
    from composition.dependencies import get_firebase_auth_provider, get_token_blacklist

    return LogoutUseCase(get_firebase_auth_provider(), get_token_blacklist())


def _get_delete_account_use_case() -> DeleteAccountUseCase:
    from composition.dependencies import (
        get_cleanup_registry,
        get_firebase_auth_provider,
        get_user_repository,
    )

    return DeleteAccountUseCase(
        get_cleanup_registry(),
        get_user_repository(),
        get_firebase_auth_provider(),
    )


def _get_get_profile_use_case() -> GetProfileUseCase:
    from composition.dependencies import get_user_repository

    return GetProfileUseCase(get_user_repository())


@router.post("/sync", response_model=UserProfileResponse)
async def sync_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> UserProfileResponse:
    use_case = _get_sync_use_case()
    data = await use_case.execute(current_user)
    return UserProfileResponse(**data)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> MessageResponse:
    authorization = request.headers.get("Authorization", "")
    token = authorization.removeprefix("Bearer ").strip()
    use_case = _get_logout_use_case()
    await use_case.execute(token)
    return MessageResponse(message="Logged out successfully")


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> None:
    use_case = _get_delete_account_use_case()
    await use_case.execute(current_user.uid)


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> UserProfileResponse:
    use_case = _get_get_profile_use_case()
    data = await use_case.execute(current_user.uid)
    return UserProfileResponse(**data)
