from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    from modules.auth.infrastructure.http.router import router as auth_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
