"""Use case: link Steam account by URL/vanity/SteamID64."""

import re

from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.services.i_steam_auth_client import ISteamAuthClient
from modules.platforms.domain.interfaces.use_cases.link_steam_manual import (
    ILinkSteamManualUseCase,
)
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.exceptions import BadRequestException

_STEAM_ID_64_RE = re.compile(r"^\d{17}$")
_STEAM_PROFILE_RE = re.compile(r"steamcommunity\.com/profiles/(\d{17})/?$")
_STEAM_VANITY_RE = re.compile(r"steamcommunity\.com/id/([^/]+)/?$")


class LinkSteamManualUseCase(ILinkSteamManualUseCase):
    """Resolve SteamID and create a Steam platform link."""

    def __init__(self, steam_client: ISteamAuthClient, repo: IPlatformRepository) -> None:
        self._steam = steam_client
        self._repo = repo

    async def execute(self, uid: str, profile_url_or_id: str) -> LinkedPlatform:
        if await self._repo.is_linked(uid, Platform.STEAM):
            raise PlatformAlreadyLinkedException("steam")

        steam_id = await self._resolve_steam_id(profile_url_or_id)
        player = await self._steam.get_player_summary(steam_id)
        username = player.persona_name if player else steam_id
        avatar_url = player.avatar_url if player else None

        linked = LinkedPlatform(
            platform=Platform.STEAM,
            username=username,
            avatar_url=avatar_url,
        )
        await self._repo.link(uid, linked)
        await self._repo.store_tokens(uid, Platform.STEAM, {"steam_id": steam_id})
        return linked

    async def _resolve_steam_id(self, value: str) -> str:
        text = value.strip()
        if not text:
            raise BadRequestException("profileUrlOrId is required")

        if _STEAM_ID_64_RE.match(text):
            return text

        profile_match = _STEAM_PROFILE_RE.search(text)
        if profile_match:
            return profile_match.group(1)

        vanity_match = _STEAM_VANITY_RE.search(text)
        vanity = vanity_match.group(1) if vanity_match else text
        steam_id = await self._steam.resolve_vanity_url(vanity)
        if steam_id is None:
            raise BadRequestException("Could not resolve Steam profile to a valid SteamID")
        return steam_id
