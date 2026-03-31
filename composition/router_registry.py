"""Central router registration for all API modules.

Each module's router is imported and mounted here with its versioned
prefix and OpenAPI tag.
"""

from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    """Import and mount all module routers onto the FastAPI application."""
    from modules.auth.infrastructure.http.router import router as auth_router
    from modules.platforms.infrastructure.http.router import router as platforms_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(platforms_router, prefix="/api/v1/platforms", tags=["platforms"])
