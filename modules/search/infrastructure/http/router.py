"""Search module HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from composition.dependencies import get_search_games_use_case
from composition.security import get_current_user
from modules.search.domain.interfaces.use_cases.search_games import ISearchGamesUseCase
from modules.search.infrastructure.http.schemas import SearchResponse, SearchResultResponse
from shared.domain.entities.user import AuthenticatedUser

router = APIRouter()


@router.get("", response_model=SearchResponse)
async def search_games(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[ISearchGamesUseCase, Depends(get_search_games_use_case)],
    q: Annotated[str, Query(min_length=1)],
) -> SearchResponse:
    results = await use_case.execute(current_user.uid, q)
    payload = [
        SearchResultResponse(
            id=item.id,
            title=item.title,
            cover_url=item.cover_url,
            steam_app_id=item.steam_app_id,
            is_owned=item.is_owned,
            owned_platforms=item.owned_platforms,
            is_in_wishlist=item.is_in_wishlist,
        )
        for item in results
    ]
    return SearchResponse(results=payload)
