"""Platforms module HTTP endpoints.

Provides routes for linking and unlinking gaming platform accounts
(Steam, Epic, GOG, PSN) and retrieving linked platforms for the
authenticated user.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition.dependencies import (
    get_epic_auth_client,
    get_get_linked_platforms_use_case,
    get_gog_auth_client,
    get_link_epic_use_case,
    get_link_gog_use_case,
    get_link_psn_use_case,
    get_link_steam_use_case,
    get_psn_auth_client,
    get_steam_auth_client,
    get_unlink_platform_use_case,
)
from composition.security import get_current_user
from modules.platforms.domain.interfaces.use_cases.get_linked_platforms import (
    IGetLinkedPlatformsUseCase,
)
from modules.platforms.domain.interfaces.use_cases.link_epic import ILinkEpicUseCase
from modules.platforms.domain.interfaces.use_cases.link_gog import ILinkGogUseCase
from modules.platforms.domain.interfaces.use_cases.link_psn import ILinkPsnUseCase
from modules.platforms.domain.interfaces.use_cases.link_steam import ILinkSteamUseCase
from modules.platforms.domain.interfaces.use_cases.unlink_platform import (
    IUnlinkPlatformUseCase,
)
from modules.platforms.infrastructure.http.schemas import (
    LinkCodeRequest,
    LinkedPlatformResponse,
    LinkPsnRequest,
    LinkSteamRequest,
    OAuthAuthUrlResponse,
    SteamAuthUrlResponse,
)
from shared.domain.entities.user import AuthenticatedUser
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.epic_auth_client import IEpicAuthClient
from shared.domain.interfaces.gog_auth_client import IGogAuthClient
from shared.domain.interfaces.psn_auth_client import IPsnAuthClient
from shared.domain.interfaces.steam_auth_client import ISteamAuthClient

router = APIRouter()


@router.get("", response_model=list[LinkedPlatformResponse])
async def get_linked_platforms(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetLinkedPlatformsUseCase, Depends(get_get_linked_platforms_use_case)],
) -> list[LinkedPlatformResponse]:
    platforms = await use_case.execute(current_user.uid)
    return [LinkedPlatformResponse(**vars(p)) for p in platforms]


@router.delete("/{platform}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_platform(
    platform: Platform,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IUnlinkPlatformUseCase, Depends(get_unlink_platform_use_case)],
) -> None:
    await use_case.execute(current_user.uid, platform)


# ---------------------------------------------------------------------------
# Steam
# ---------------------------------------------------------------------------


@router.get("/steam/auth-url", response_model=SteamAuthUrlResponse)
async def steam_auth_url(
    return_url: str,
    steam_client: Annotated[ISteamAuthClient, Depends(get_steam_auth_client)],
) -> SteamAuthUrlResponse:
    url = steam_client.build_openid_url(return_url)
    return SteamAuthUrlResponse(url=url)


@router.post(
    "/steam/link", response_model=LinkedPlatformResponse, status_code=status.HTTP_201_CREATED
)
async def link_steam(
    body: LinkSteamRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ILinkSteamUseCase, Depends(get_link_steam_use_case)],
) -> LinkedPlatformResponse:
    linked = await use_case.execute(current_user.uid, body.openid_params)
    return LinkedPlatformResponse(**vars(linked))


# ---------------------------------------------------------------------------
# Epic Games
# ---------------------------------------------------------------------------


@router.get("/epic/auth-url", response_model=OAuthAuthUrlResponse)
async def epic_auth_url(
    epic_client: Annotated[IEpicAuthClient, Depends(get_epic_auth_client)],
) -> OAuthAuthUrlResponse:
    url = epic_client.build_login_url()
    return OAuthAuthUrlResponse(url=url)


@router.post(
    "/epic/link", response_model=LinkedPlatformResponse, status_code=status.HTTP_201_CREATED
)
async def link_epic(
    body: LinkCodeRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ILinkEpicUseCase, Depends(get_link_epic_use_case)],
) -> LinkedPlatformResponse:
    linked = await use_case.execute(current_user.uid, body.code)
    return LinkedPlatformResponse(**vars(linked))


# ---------------------------------------------------------------------------
# GOG
# ---------------------------------------------------------------------------


@router.get("/gog/auth-url", response_model=OAuthAuthUrlResponse)
async def gog_auth_url(
    gog_client: Annotated[IGogAuthClient, Depends(get_gog_auth_client)],
) -> OAuthAuthUrlResponse:
    url = gog_client.build_auth_url()
    return OAuthAuthUrlResponse(url=url)


@router.post(
    "/gog/link", response_model=LinkedPlatformResponse, status_code=status.HTTP_201_CREATED
)
async def link_gog(
    body: LinkCodeRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ILinkGogUseCase, Depends(get_link_gog_use_case)],
) -> LinkedPlatformResponse:
    linked = await use_case.execute(current_user.uid, body.code)
    return LinkedPlatformResponse(**vars(linked))


# ---------------------------------------------------------------------------
# PSN
# ---------------------------------------------------------------------------


@router.get("/psn/auth-url", response_model=OAuthAuthUrlResponse)
async def psn_auth_url(
    psn_client: Annotated[IPsnAuthClient, Depends(get_psn_auth_client)],
) -> OAuthAuthUrlResponse:
    url = psn_client.build_login_url()
    return OAuthAuthUrlResponse(url=url)


@router.post(
    "/psn/link", response_model=LinkedPlatformResponse, status_code=status.HTTP_201_CREATED
)
async def link_psn(
    body: LinkPsnRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ILinkPsnUseCase, Depends(get_link_psn_use_case)],
) -> LinkedPlatformResponse:
    linked = await use_case.execute(current_user.uid, body.npsso)
    return LinkedPlatformResponse(**vars(linked))
