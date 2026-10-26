from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.observability import Metrics
from app.main import app
from app.models.audit_event import AuditEvent
from app.services.retention import run_retention


def test_security_headers_and_metrics() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "fraudlens_http_requests_total" in TestClient(app).get("/metrics").text
    assert Metrics.requests


def test_oversized_request_is_rejected() -> None:
    settings = get_settings()
    original = settings.max_request_body_bytes
    settings.max_request_body_bytes = 10_000
    try:
        response = TestClient(app).post(
            "/v1/transactions/score",
            content=b"x" * 10_001,
            headers={"Content-Type": "application/json"},
        )
    finally:
        settings.max_request_body_bytes = original
    assert response.status_code == 413


def test_retention_removes_expired_records(db_session: Session) -> None:
    event = AuditEvent(
        tenant_id=None,
        actor_type="test",
        action="test",
        target_type="test",
        details_redacted={},
        created_at=datetime.now(UTC) - timedelta(days=10),
    )
    db_session.add(event)
    db_session.commit()
    result = run_retention(
        db_session,
        Settings(app_env="test", retention_audit_days=1, api_key_hash_pepper="test-pepper"),
    )
    assert result["audit_events"] == 1
    assert db_session.scalar(select(AuditEvent).where(AuditEvent.id == event.id)) is None
