"""FraudLens FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.alerts import router as alerts_router
from app.api.audit import router as audit_router
from app.api.config import router as config_router
from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.transactions import router as transactions_router
from app.api.webhooks import router as webhooks_router
from app.core.config import get_settings
from app.core.correlation import CorrelationIdMiddleware
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unexpected_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging
from app.core.observability import (
    RequestGuardMiddleware,
    SecurityHeadersMiddleware,
    metrics_response,
)

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="FraudLens API",
    description="Integration-first fraud intelligence platform.",
    version="0.1.0",
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestGuardMiddleware, settings=settings)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-ID"],
)
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unexpected_error_handler)
app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(alerts_router)
app.include_router(audit_router)
app.include_router(config_router)
app.include_router(events_router)
app.include_router(webhooks_router)


@app.get("/metrics", include_in_schema=False)
def metrics() -> PlainTextResponse:
    return metrics_response()


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Return service metadata."""

    return {"service": "fraudlens-api", "status": "foundation", "version": "0.1.0"}
