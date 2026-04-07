from typing import Any

from fastapi import Request
from httpx import ASGITransport, AsyncClient
from pytest import MonkeyPatch
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from main import create_app


async def test_rate_limiter_connection_error_returns_503(monkeypatch: MonkeyPatch) -> None:
    async def raise_connection_error(
        self: Any, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        raise ConnectionError("redis unavailable")

    monkeypatch.setattr(SlowAPIMiddleware, "dispatch", raise_connection_error)

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "code": "RATE_LIMITER_UNAVAILABLE",
        "message": "Rate limiter unavailable.",
        "detail": None,
    }
