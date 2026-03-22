"""Structured exception hierarchy and global exception handlers.

All domain exceptions inherit from AppException, which carries an HTTP status
code, a machine-readable error code, and a human-readable message. The handlers
at the bottom of this module convert exceptions into consistent JSON responses.
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for all application-level errors.

    Args:
        status_code: HTTP status code to return.
        code: Machine-readable error code (e.g. "NOT_FOUND").
        message: Human-readable error description.
        detail: Optional additional context for debugging.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        detail: Any = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)


class BadRequestException(AppException):
    """Raised when the client sends invalid or malformed input (400)."""

    def __init__(self, message: str = "Bad request", detail: Any = None) -> None:
        super().__init__(400, "BAD_REQUEST", message, detail)


class UnauthorizedException(AppException):
    """Raised when authentication fails or is missing (401)."""

    def __init__(self, message: str = "Unauthorized", detail: Any = None) -> None:
        super().__init__(401, "UNAUTHORIZED", message, detail)


class ForbiddenException(AppException):
    """Raised when the user lacks permission for the requested action (403)."""

    def __init__(self, message: str = "Forbidden", detail: Any = None) -> None:
        super().__init__(403, "FORBIDDEN", message, detail)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist (404)."""

    def __init__(self, message: str = "Not found", detail: Any = None) -> None:
        super().__init__(404, "NOT_FOUND", message, detail)


class ConflictException(AppException):
    """Raised when the request conflicts with current state (409)."""

    def __init__(self, message: str = "Conflict", detail: Any = None) -> None:
        super().__init__(409, "CONFLICT", message, detail)


class RateLimitedException(AppException):
    """Raised when a rate limit has been exceeded (429)."""

    def __init__(self, message: str = "Rate limited", detail: Any = None) -> None:
        super().__init__(429, "RATE_LIMITED", message, detail)


class ExternalServiceException(AppException):
    """Raised when a third-party service returns an error (502)."""

    def __init__(self, message: str = "External service error", detail: Any = None) -> None:
        super().__init__(502, "EXTERNAL_SERVICE_ERROR", message, detail)


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert AppException instances into structured JSON error responses."""
    if isinstance(exc, AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
            },
        )
    return JSONResponse(
        status_code=500, content={"code": "INTERNAL_ERROR", "message": "Internal server error"}
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler that prevents raw tracebacks from leaking to clients."""
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "Internal server error"},
    )
