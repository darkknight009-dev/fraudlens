"""Correlation ID middleware."""

import re
import uuid

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

CORRELATION_HEADER = "X-Correlation-ID"
CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex}"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get(CORRELATION_HEADER)
        request_id = (
            supplied if supplied and CORRELATION_PATTERN.fullmatch(supplied) else new_request_id()
        )
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response: Response
        if supplied and supplied != request_id:
            response = JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "INVALID_CORRELATION_ID",
                        "message": "X-Correlation-ID is invalid.",
                        "details": [],
                        "request_id": request_id,
                    }
                },
            )
        else:
            response = await call_next(request)

        response.headers[CORRELATION_HEADER] = request_id
        structlog.contextvars.clear_contextvars()
        return response
