"""Operational health and readiness endpoints."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
def ready(request: Request, session: Session = Depends(get_db)) -> JSONResponse:  # noqa: B008
    request_id = request.state.request_id
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "dependencies": {"database": "unavailable"},
                "request_id": request_id,
            },
            headers={"X-Correlation-ID": request_id},
        )
    return JSONResponse(
        content={"status": "ready", "dependencies": {"database": "ok"}, "request_id": request_id},
        headers={"X-Correlation-ID": request_id},
    )
