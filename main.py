"""GameShelf API application factory and entry point.

Configures the FastAPI app with CORS, exception handlers, lifespan
management for Redis/Firebase connections, and module router registration.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from shared.config import get_settings
from shared.exceptions import AppException, app_exception_handler, unhandled_exception_handler
from shared.infrastructure.http.rate_limiter import (
    RateLimiterBackendConnectionError,
    limiter,
    rate_limit_exceeded_handler,
    rate_limiter_connection_error_handler,
)
from shared.infrastructure.http.security_headers_middleware import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of external connections (Redis, Firebase)."""
    settings = get_settings()
    if not settings.is_testing:
        try:
            from shared.infrastructure.cache.redis_client import init_redis

            await init_redis()
        except Exception:
            pass
        try:
            from shared.infrastructure.security.firebase_client import get_firebase_app

            get_firebase_app()
        except Exception:
            pass
    yield
    if not settings.is_testing:
        try:
            from shared.infrastructure.cache.redis_client import close_redis

            await close_redis()
        except Exception:
            pass


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(title="GameShelf API", lifespan=lifespan)

    # Attach the rate limiter singleton to app state so SlowAPIMiddleware can
    # locate it on every request without going through dependency injection.
    app.state.limiter = limiter

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_exception_handler(
        RateLimiterBackendConnectionError, rate_limiter_connection_error_handler
    )
    app.add_exception_handler(ConnectionError, rate_limiter_connection_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    from composition.router_registry import register_routers

    register_routers(app)

    return app


app = create_app()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
