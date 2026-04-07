from httpx import ASGITransport, AsyncClient

from main import create_app
from shared.infrastructure.http import rate_limiter


async def test_rate_limiter_connection_error_returns_503(monkeypatch) -> None:
    async def raise_connection_error(self, request, call_next):
        raise ConnectionError("redis unavailable")

    monkeypatch.setattr(rate_limiter.SlowAPIMiddleware, "dispatch", raise_connection_error)

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "code": "RATE_LIMITER_UNAVAILABLE",
        "message": "Rate limiter unavailable.",
        "detail": None,
    }
