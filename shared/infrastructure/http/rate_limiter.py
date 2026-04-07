"""API-level rate limiter using slowapi backed by Redis.

Provides a per-IP request rate limiter that integrates with FastAPI via
``SlowAPIMiddleware``. Limits are enforced globally across all routes using
the default limit configured in ``Settings.api_rate_limit``.

In testing mode the limiter uses in-memory storage to avoid requiring a live
Redis instance during the test suite.

Usage in ``main.py``::

    from shared.infrastructure.http.rate_limiter import SafeSlowAPIMiddleware

    from shared.infrastructure.http.rate_limiter import limiter, rate_limit_exceeded_handler

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SafeSlowAPIMiddleware)
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from shared.config import get_settings

_settings = get_settings()

# Use in-memory storage during tests so the test suite requires no Redis.
# In all other environments the Upstash Redis URL is used as the shared
# counter store, ensuring limits are consistent across multiple workers.
_storage_uri = None if _settings.is_testing else _settings.redis_url

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_settings.api_rate_limit],
    storage_uri=_storage_uri,
)
"""Module-level ``Limiter`` singleton.

Must be assigned to ``app.state.limiter`` so that ``SlowAPIMiddleware`` can
locate it at request time. The same instance can also be used as a decorator
on individual routes when per-endpoint limits are needed::

    @router.get("/example")
    @limiter.limit("10/minute")
    async def example(request: Request) -> dict[str, str]:
        ...
"""


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert a ``RateLimitExceeded`` error into a structured JSON 429 response.

    slowapi raises ``RateLimitExceeded`` (not an ``AppException``) when a
    client exceeds its quota. This handler formats that error using the same
    JSON envelope as the rest of the API so clients receive a consistent shape.

    Args:
        request: The incoming HTTP request that triggered the limit.
        exc: The ``RateLimitExceeded`` exception raised by slowapi.

    Returns:
        A ``JSONResponse`` with status 429 and a machine-readable error body.
    """
    if isinstance(exc, RateLimitExceeded):
        detail = str(exc.detail) if exc.detail else None
    else:
        detail = None

    return JSONResponse(
        status_code=429,
        content={
            "code": "RATE_LIMITED",
            "message": "Too many requests. Please slow down.",
            "detail": detail,
        },
    )


async def rate_limiter_connection_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Convert rate limiter backend failures into a structured JSON 503 response."""
    return JSONResponse(
        status_code=503,
        content={
            "code": "RATE_LIMITER_UNAVAILABLE",
            "message": "Rate limiter unavailable.",
            "detail": None,
        },
    )


class SafeSlowAPIMiddleware(SlowAPIMiddleware):
    """Prevent slowapi connection failures from crashing the whole request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await super().dispatch(request, call_next)
        except ConnectionError as exc:
            return await rate_limiter_connection_error_handler(request, exc)
