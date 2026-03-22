from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from shared.exceptions import AppException, app_exception_handler, unhandled_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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
    settings = get_settings()

    app = FastAPI(title="GameShelf API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    from composition.router_registry import register_routers

    register_routers(app)

    return app


app = create_app()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
