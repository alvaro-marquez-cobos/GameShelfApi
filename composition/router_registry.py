"""Central router registration for all API modules.

Each module's router is imported and mounted here with its versioned
prefix and OpenAPI tag.
"""

from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    """Import and mount all module routers onto the FastAPI application."""
    from modules.auth.infrastructure.http.router import router as auth_router
    from modules.games.infrastructure.http.router import router as games_router
    from modules.home.infrastructure.http.router import router as home_router
    from modules.library.infrastructure.http.router import router as library_router
    from modules.platforms.infrastructure.http.router import router as platforms_router
    from modules.search.infrastructure.http.router import router as search_router
    from modules.settings.infrastructure.http.router import router as settings_router
    from modules.wishlist.infrastructure.http.router import router as wishlist_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(library_router, prefix="/api/v1/library", tags=["library"])
    app.include_router(games_router, prefix="/api/v1/games", tags=["games"])
    app.include_router(search_router, prefix="/api/v1/search", tags=["search"])
    app.include_router(wishlist_router, prefix="/api/v1/wishlist", tags=["wishlist"])
    app.include_router(platforms_router, prefix="/api/v1/platforms", tags=["platforms"])
    app.include_router(home_router, prefix="/api/v1/home", tags=["home"])
    app.include_router(settings_router, prefix="/api/v1/settings", tags=["settings"])
