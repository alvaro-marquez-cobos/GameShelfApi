"""Wishlist module HTTP endpoints."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition.dependencies import (
    get_add_to_wishlist_use_case,
    get_check_wishlist_use_case,
    get_get_wishlist_use_case,
    get_remove_from_wishlist_use_case,
)
from composition.security import get_current_user
from modules.wishlist.domain.entities.wishlist_item import WishlistItem
from modules.wishlist.domain.interfaces.use_cases.add_to_wishlist import IAddToWishlistUseCase
from modules.wishlist.domain.interfaces.use_cases.check_wishlist import ICheckWishlistUseCase
from modules.wishlist.domain.interfaces.use_cases.get_wishlist import IGetWishlistUseCase
from modules.wishlist.domain.interfaces.use_cases.remove_from_wishlist import (
    IRemoveFromWishlistUseCase,
)
from modules.wishlist.infrastructure.http.schemas import (
    AddWishlistRequest,
    CheckWishlistResponse,
    GetWishlistResponse,
    WishlistItemResponse,
)
from shared.domain.entities.user import AuthenticatedUser
from shared.domain.enums.platform import Platform
from shared.exceptions import BadRequestException

router = APIRouter()


def _best_deal_percentage(deals: list[object]) -> int | None:
    if not deals:
        return None
    best = max(getattr(deal, "discount", 0) for deal in deals)
    return int(best)


def _infer_platform(game_id: str, steam_app_id: int | None) -> tuple[str, Platform]:
    parts = game_id.split("_", 1)
    prefix = parts[0] if len(parts) > 1 else ""
    try:
        platform = Platform.from_raw(prefix)
        return game_id, platform
    except ValueError as err:
        if steam_app_id is not None:
            return f"steam_{steam_app_id}", Platform.STEAM
        raise BadRequestException("Could not infer platform from gameId") from err


@router.get("", response_model=GetWishlistResponse)
async def get_wishlist(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IGetWishlistUseCase, Depends(get_get_wishlist_use_case)],
) -> GetWishlistResponse:
    rows = await use_case.execute(current_user.uid)
    return GetWishlistResponse(
        items=[
            WishlistItemResponse(
                id=item.game_id,
                game_id=item.game_id,
                title=item.title,
                platform=item.platform,
                cover_url=item.cover_url,
                added_at=item.added_at,
                best_deal_percentage=_best_deal_percentage(deals),
            )
            for item, deals in rows
        ]
    )


@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    body: AddWishlistRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IAddToWishlistUseCase, Depends(get_add_to_wishlist_use_case)],
) -> WishlistItemResponse:
    normalized_game_id, platform = _infer_platform(body.game_id, body.steam_app_id)
    item = WishlistItem(
        game_id=normalized_game_id,
        title=body.title,
        platform=platform,
        cover_url=body.cover_url,
        added_at=datetime.now(UTC).isoformat(),
    )
    await use_case.execute(current_user.uid, item)
    return WishlistItemResponse(
        id=item.game_id,
        game_id=item.game_id,
        title=item.title,
        platform=item.platform,
        cover_url=item.cover_url,
        added_at=item.added_at,
        best_deal_percentage=None,
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(
    item_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[IRemoveFromWishlistUseCase, Depends(get_remove_from_wishlist_use_case)],
) -> None:
    await use_case.execute(current_user.uid, item_id)


@router.get("/check/{game_id}", response_model=CheckWishlistResponse)
async def check_wishlist(
    game_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ICheckWishlistUseCase, Depends(get_check_wishlist_use_case)],
) -> CheckWishlistResponse:
    return CheckWishlistResponse(is_in_wishlist=await use_case.execute(current_user.uid, game_id))
