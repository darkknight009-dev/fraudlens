from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app


def test_liveness_does_not_require_database() -> None:
    response = TestClient(app).get("/health/live", headers={"X-Correlation-ID": "req_test_123"})

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
    assert response.headers["X-Correlation-ID"] == "req_test_123"


def test_invalid_correlation_id_uses_safe_error_envelope() -> None:
    response = TestClient(app).get("/health/live", headers={"X-Correlation-ID": "bad value"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CORRELATION_ID"
    assert response.json()["error"]["request_id"].startswith("req_")


def test_readiness_reports_database_ready() -> None:
    class HealthySession:
        def execute(self, statement: object) -> None:
            del statement

    def healthy_db() -> Iterator[HealthySession]:
        yield HealthySession()

    app.dependency_overrides[get_db] = healthy_db
    try:
        response = TestClient(app).get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["dependencies"] == {"database": "ok"}


def test_readiness_reports_database_failure_without_internal_details() -> None:
    class BrokenSession:
        def execute(self, statement: object) -> None:
            del statement
            raise SQLAlchemyError("database unavailable")

    def broken_db() -> Iterator[BrokenSession]:
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        response = TestClient(app).get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["dependencies"] == {"database": "unavailable"}
    assert "password" not in response.text.lower()
