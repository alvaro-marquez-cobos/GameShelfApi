from httpx import ASGITransport, AsyncClient
from pytest import MonkeyPatch

from main import app
from shared.infrastructure.http.rate_limiter import RateLimiterBackendConnectionError, limiter


async def test_rate_limiter_connection_error_returns_503(monkeypatch: MonkeyPatch) -> None:
    def raise_connection_error(*args: object, **kwargs: object) -> None:
        raise RateLimiterBackendConnectionError("redis unavailable")

    monkeypatch.setattr(limiter, "_check_request_limit", raise_connection_error)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "code": "RATE_LIMITER_UNAVAILABLE",
        "message": "Rate limiter unavailable.",
        "detail": "redis unavailable",
    }
