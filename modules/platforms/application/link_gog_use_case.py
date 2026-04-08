"""Use case: link a GOG account via OAuth2 authorization code."""

from datetime import UTC, datetime

from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.use_cases.link_gog import ILinkGogUseCase
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.gog_auth_client import IGogAuthClient


class LinkGogUseCase(ILinkGogUseCase):
    """Exchange the GOG auth code and persist the linked account."""

    def __init__(self, gog_client: IGogAuthClient, repo: IPlatformRepository) -> None:
        self._gog = gog_client
        self._repo = repo

    async def execute(self, uid: str, code: str) -> LinkedPlatform:
        token = await self._gog.exchange_code(code)

        if await self._repo.is_linked(uid, Platform.GOG):
            raise PlatformAlreadyLinkedException("gog")

        linked = LinkedPlatform(
            platform=Platform.GOG,
            username=token.user_id,
            linked_at=datetime.now(UTC).isoformat(),
        )
        await self._repo.link(uid, linked)
        await self._repo.store_tokens(
            uid,
            Platform.GOG,
            {
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "user_id": token.user_id,
                "expires_at": token.expires_at,
            },
        )
        return linked
