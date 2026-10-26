"""Minimal operational metrics and request guards for the modular monolith."""

from collections import Counter, defaultdict, deque
from time import monotonic
from typing import ClassVar

from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import Settings


class Metrics:
    """Process-local metrics; production aggregation belongs at the deployment edge."""

    requests: ClassVar[Counter[str]] = Counter()
    durations: ClassVar[defaultdict[str, list[float]]] = defaultdict(list)

    @classmethod
    def observe(cls, route: str, status_code: int, duration_ms: float) -> None:
        cls.requests[f"{route}|{status_code}"] += 1
        cls.durations[route].append(duration_ms)

    @classmethod
    def prometheus(cls) -> str:
        lines = [
            "# HELP fraudlens_http_requests_total HTTP requests by route and status.",
            "# TYPE fraudlens_http_requests_total counter",
        ]
        for key, count in sorted(cls.requests.items()):
            route, status = key.rsplit("|", 1)
            lines.append(
                f'fraudlens_http_requests_total{{route="{route}",status="{status}"}} {count}'
            )
        lines.extend(
            [
                "# HELP fraudlens_http_request_duration_ms_count Observed request durations.",
                "# TYPE fraudlens_http_request_duration_ms_count counter",
            ]
        )
        for route, values in sorted(cls.durations.items()):
            lines.append(
                f'fraudlens_http_request_duration_ms_count{{route="{route}"}} {len(values)}'
            )
        return "\n".join(lines) + "\n"


class RequestGuardMiddleware(BaseHTTPMiddleware):
    """Reject oversized requests and apply a bounded process-local rate limit."""

    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings
        self._requests: defaultdict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = getattr(request.state, "request_id", "req_unknown")
        content_length = request.headers.get("content-length")
        try:
            declared_length = int(content_length) if content_length is not None else 0
        except ValueError:
            declared_length = self.settings.max_request_body_bytes + 1
        if declared_length > self.settings.max_request_body_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "REQUEST_TOO_LARGE",
                        "message": "Request body exceeds the configured limit.",
                        "details": [],
                        "request_id": request_id,
                    }
                },
            )
        now = monotonic()
        client_id = request.client.host if request.client else "unknown"
        window = self._requests[client_id]
        while window and window[0] <= now - 60:
            window.popleft()
        if len(window) >= self.settings.rate_limit_requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Request rate limit exceeded.",
                        "details": [],
                        "request_id": request_id,
                    }
                },
                headers={"Retry-After": "60"},
            )
        window.append(now)
        started = monotonic()
        response = await call_next(request)
        Metrics.observe(request.url.path, response.status_code, (monotonic() - started) * 1000)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response


def metrics_response() -> PlainTextResponse:
    return PlainTextResponse(Metrics.prometheus(), media_type="text/plain; version=0.0.4")
