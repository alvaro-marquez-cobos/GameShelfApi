"""Games module HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from composition.dependencies import get_get_game_detail_use_case, get_get_game_dlcs_use_case
from composition.security import get_current_user
from modules.games.domain.interfaces.use_cases.get_game_detail import IGetGameDetailUseCase
from modules.games.domain.interfaces.use_cases.get_game_dlcs import IGetGameDlcsUseCase
from modules.games.infrastructure.http.schemas import (
    DealResponse,
    DlcResponse,
    GameDetailResponse,
    GameSummaryResponse,
    GetGameDlcsResponse,
    HowLongToBeatResponse,
    ProtonDbResponse,
    SteamMetadataResponse,
)
from shared.domain.entities.user import AuthenticatedUser
from shared.domain.enums.platform import Platform

router = APIRouter()


@router.get("/{game_id}", response_model=GameDetailResponse)
async def get_game_detail(
    game_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetGameDetailUseCase, Depends(get_get_game_detail_use_case)],
    platform: Annotated[Platform | None, Query()] = None,
) -> GameDetailResponse:
    detail = await use_case.execute(current_user.uid, game_id, platform=platform)

    proton_db = None
    if detail.protondb is not None:
        proton_db = ProtonDbResponse(
            tier=detail.protondb.tier,
            trendingTier=detail.protondb.trending_tier,
            totalReports=detail.protondb.total,
        )

    hltb = None
    if detail.hltb is not None:
        hltb = HowLongToBeatResponse(
            mainHours=detail.hltb.main_story,
            mainExtraHours=detail.hltb.main_extra,
            completionistHours=detail.hltb.completionist,
        )

    steam_metadata = None
    if detail.steam is not None:
        steam_metadata = SteamMetadataResponse(
            genres=detail.steam.genres,
            developers=detail.steam.developers,
            publishers=detail.steam.publishers,
            releaseDate=detail.steam.release_date,
            metacriticScore=detail.steam.metacritic_score,
            recommendationCount=detail.steam.recommendation_count,
            screenshots=detail.steam.screenshots,
        )

    deals = [
        DealResponse(
            id=deal.id,
            storeName=deal.store_name,
            price=deal.price,
            originalPrice=deal.regular_price,
            discountPercentage=deal.discount,
            url=deal.url,
            currency=deal.currency,
        )
        for deal in detail.deals
    ]

    return GameDetailResponse(
        game=GameSummaryResponse(
            game_id=detail.game_id,
            title=detail.title,
            platform=detail.platform,
            steam_app_id=detail.steam_app_id,
            cover_url=detail.cover_url,
            portrait_cover_url=detail.portrait_cover_url,
            playtime_minutes=detail.playtime_minutes,
            last_played=detail.last_played,
            description=detail.description,
        ),
        proton_db=proton_db,
        how_long_to_beat=hltb,
        steam_metadata=steam_metadata,
        deals=deals,
        is_in_wishlist=detail.is_in_wishlist,
    )


@router.get("/{game_id}/dlcs", response_model=GetGameDlcsResponse)
async def get_game_dlcs(
    game_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetGameDlcsUseCase, Depends(get_get_game_dlcs_use_case)],
) -> GetGameDlcsResponse:
    dlcs = await use_case.execute(current_user.uid, game_id)
    return GetGameDlcsResponse(
        dlcs=[
            DlcResponse(
                appId=dlc.app_id,
                name=dlc.name,
                headerImage=dlc.header_image,
                isOwned=dlc.is_owned,
            )
            for dlc in dlcs
        ]
    )
