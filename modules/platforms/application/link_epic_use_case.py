"""Use case: link an Epic Games account via OAuth2 authorization code."""

from datetime import UTC, datetime

from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.use_cases.link_epic import ILinkEpicUseCase
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.epic_auth_client import IEpicAuthClient


class LinkEpicUseCase(ILinkEpicUseCase):
    """Exchange the Epic auth code and persist the linked account."""

    def __init__(self, epic_client: IEpicAuthClient, repo: IPlatformRepository) -> None:
        self._epic = epic_client
        self._repo = repo

    async def execute(self, uid: str, code: str) -> LinkedPlatform:
        token = await self._epic.exchange_auth_code(code)

        if await self._repo.is_linked(uid, Platform.EPIC):
            raise PlatformAlreadyLinkedException("epic")

        linked = LinkedPlatform(
            platform=Platform.EPIC,
            username=token.display_name or token.account_id,
            linked_at=datetime.now(UTC).isoformat(),
        )
        await self._repo.link(uid, linked)
        await self._repo.store_tokens(
            uid,
            Platform.EPIC,
            {
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "account_id": token.account_id,
                "expires_at": token.expires_at,
            },
        )
        return linked
