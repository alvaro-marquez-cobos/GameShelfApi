"""Use case: link a PlayStation Network account via NPSSO token."""

from datetime import UTC, datetime

from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.use_cases.link_psn import ILinkPsnUseCase
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.psn_auth_client import IPsnAuthClient


class LinkPsnUseCase(ILinkPsnUseCase):
    """Exchange the PSN NPSSO token and persist the linked account."""

    def __init__(self, psn_client: IPsnAuthClient, repo: IPlatformRepository) -> None:
        self._psn = psn_client
        self._repo = repo

    async def execute(self, uid: str, npsso: str) -> LinkedPlatform:
        token = await self._psn.exchange_npsso(npsso)

        if await self._repo.is_linked(uid, Platform.PSN):
            raise PlatformAlreadyLinkedException("psn")

        linked = LinkedPlatform(
            platform=Platform.PSN,
            username=token.account_id,
            linked_at=datetime.now(UTC).isoformat(),
        )
        await self._repo.link(uid, linked)
        await self._repo.store_tokens(
            uid,
            Platform.PSN,
            {
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "account_id": token.account_id,
                "expires_at": token.expires_at,
            },
        )
        return linked
