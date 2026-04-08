"""Use case: link a Steam account via OpenID 2.0 callback."""

from datetime import UTC, datetime

from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.use_cases.link_steam import ILinkSteamUseCase
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.steam_auth_client import ISteamAuthClient
from shared.exceptions import BadRequestException


class LinkSteamUseCase(ILinkSteamUseCase):
    """Verify the Steam OpenID callback and persist the linked account."""

    def __init__(self, steam_client: ISteamAuthClient, repo: IPlatformRepository) -> None:
        self._steam = steam_client
        self._repo = repo

    async def execute(self, uid: str, openid_params: dict[str, str]) -> LinkedPlatform:
        steam_id = await self._steam.verify_openid(openid_params)
        if steam_id is None:
            raise BadRequestException("Steam OpenID verification failed")

        if await self._repo.is_linked(uid, Platform.STEAM):
            raise PlatformAlreadyLinkedException("steam")

        player = await self._steam.get_player_summary(steam_id)
        username = player.persona_name if player else steam_id
        avatar_url = player.avatar_url if player else None

        linked = LinkedPlatform(
            platform=Platform.STEAM,
            username=username,
            avatar_url=avatar_url,
            linked_at=datetime.now(UTC).isoformat(),
        )
        await self._repo.link(uid, linked)
        await self._repo.store_tokens(uid, Platform.STEAM, {"steam_id": steam_id})
        return linked
