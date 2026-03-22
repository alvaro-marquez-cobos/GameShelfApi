from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
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
    def __init__(self, message: str = "Bad request", detail: Any = None) -> None:
        super().__init__(400, "BAD_REQUEST", message, detail)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", detail: Any = None) -> None:
        super().__init__(401, "UNAUTHORIZED", message, detail)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", detail: Any = None) -> None:
        super().__init__(403, "FORBIDDEN", message, detail)


class NotFoundException(AppException):
    def __init__(self, message: str = "Not found", detail: Any = None) -> None:
        super().__init__(404, "NOT_FOUND", message, detail)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", detail: Any = None) -> None:
        super().__init__(409, "CONFLICT", message, detail)


class RateLimitedException(AppException):
    def __init__(self, message: str = "Rate limited", detail: Any = None) -> None:
        super().__init__(429, "RATE_LIMITED", message, detail)


class ExternalServiceException(AppException):
    def __init__(self, message: str = "External service error", detail: Any = None) -> None:
        super().__init__(502, "EXTERNAL_SERVICE_ERROR", message, detail)


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
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
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "Internal server error"},
    )
