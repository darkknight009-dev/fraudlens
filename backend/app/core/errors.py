"""Public error types and the documented error envelope."""

from collections.abc import Sequence
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]]
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorPayload


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = list(details or [])


class AuthenticationError(AppError):
    def __init__(self) -> None:
        super().__init__("AUTHENTICATION_REQUIRED", "Authentication is required.", 401)


class AuthorizationError(AppError):
    def __init__(self, scope: str) -> None:
        super().__init__(
            "INSUFFICIENT_SCOPE",
            "The credential lacks the required scope.",
            403,
            [{"scope": scope}],
        )


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "req_unknown")


def error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    details: Sequence[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorPayload(
            code=code,
            message=message,
            details=list(details or []),
            request_id=_request_id(request),
        )
    ).model_dump()
    response = JSONResponse(status_code=status_code, content=body, headers=headers)
    response.headers["X-Correlation-ID"] = _request_id(request)
    return response


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return error_response(request, exc.code, exc.message, exc.status_code, exc.details, headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in error.get("loc", [])),
            "message": str(error.get("msg", "Invalid value")),
            "type": str(error.get("type", "validation_error")),
        }
        for error in exc.errors()
    ]
    return error_response(request, "VALIDATION_ERROR", "Request validation failed.", 422, details)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status_codes = {401: "AUTHENTICATION_REQUIRED", 403: "FORBIDDEN", 404: "NOT_FOUND"}
    code = status_codes.get(exc.status_code, "HTTP_ERROR")
    message = str(exc.detail) if isinstance(exc.detail, str) else "Request could not be completed."
    return error_response(request, code, message, exc.status_code)


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del exc
    return error_response(request, "INTERNAL_ERROR", "An unexpected error occurred.", 500)
