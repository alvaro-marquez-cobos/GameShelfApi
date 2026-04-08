"""Use case: link Epic account using GDPR JSON export."""

from modules.library.domain.interfaces.repositories.i_library_repository import (
    ILibraryRepository,
)
from modules.platforms.domain.exceptions import PlatformAlreadyLinkedException
from modules.platforms.domain.interfaces.repositories.i_platform_repository import (
    IPlatformRepository,
)
from modules.platforms.domain.interfaces.use_cases.link_epic_gdpr import (
    ILinkEpicGdprUseCase,
)
from shared.domain.entities.library_game import LibraryGame
from shared.domain.entities.linked_platform import LinkedPlatform
from shared.domain.enums.platform import Platform
from shared.domain.interfaces.epic_auth_client import IEpicAuthClient
from shared.exceptions import BadRequestException


class LinkEpicGdprUseCase(ILinkEpicGdprUseCase):
    """Parse GDPR export, import Epic games, and mark Epic as linked."""

    def __init__(
        self,
        epic_client: IEpicAuthClient,
        platform_repo: IPlatformRepository,
        library_repo: ILibraryRepository,
    ) -> None:
        self._epic = epic_client
        self._platform_repo = platform_repo
        self._library_repo = library_repo

    async def execute(self, uid: str, json_content: str) -> LinkedPlatform:
        if await self._platform_repo.is_linked(uid, Platform.EPIC):
            raise PlatformAlreadyLinkedException("epic")

        games = self._epic.parse_gdpr_export(json_content)
        if not games:
            raise BadRequestException("No games found in Epic GDPR export")

        library_games = [
            LibraryGame(
                game_id=f"epic_{game.namespace}_{game.app_name}",
                title=game.app_name,
                platform=Platform.EPIC,
                extra={
                    "namespace": game.namespace,
                    "catalog_item_id": game.catalog_item_id,
                },
            )
            for game in games
        ]
        await self._library_repo.upsert_games(uid, library_games)

        linked = LinkedPlatform(platform=Platform.EPIC, username="imported")
        await self._platform_repo.link(uid, linked)
        return linked
