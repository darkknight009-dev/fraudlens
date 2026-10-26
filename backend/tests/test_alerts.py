from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import app
from app.models.alert import Alert
from app.models.api_key import APIKey, APIKeyScope
from app.models.audit_event import AuditEvent
from app.models.tenant import Tenant
from app.services.auth import generate_api_key


def alert_settings() -> Settings:
    return Settings(app_env="test", api_key_hash_pepper="test-pepper-with-at-least-32-characters")


@pytest.fixture()
def alert_client(db_session: Session) -> Iterator[tuple[TestClient, str, Session, Tenant]]:
    tenant = Tenant(name="Alert Tenant")
    db_session.add(tenant)
    db_session.commit()
    generated = generate_api_key(alert_settings().api_key_hash_pepper)
    db_session.add(
        APIKey(
            tenant_id=tenant.id,
            key_prefix=generated.prefix,
            key_hash=generated.digest,
            created_by="test",
            scopes=[
                APIKeyScope(scope="transactions:score"),
                APIKeyScope(scope="cases:read"),
                APIKeyScope(scope="cases:write"),
            ],
        )
    )
    db_session.commit()

    def override_db() -> Session:
        return db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = alert_settings
    try:
        yield TestClient(app), generated.plaintext, db_session, tenant
    finally:
        app.dependency_overrides.clear()


def high_risk_payload(transaction_id: str) -> dict[str, object]:
    return {
        "transaction_id": transaction_id,
        "amount_minor": 2_000_000,
        "currency": "INR",
        "occurred_at": "2026-10-26T15:30:00Z",
        "account_ref": "acct_alert_1",
        "channel": "card",
        "provider_status": "declined",
    }


AlertFixture = tuple[TestClient, str, Session, Tenant]


def test_high_risk_score_creates_deduplicated_alert(alert_client: AlertFixture) -> None:
    client, key, session, tenant = alert_client
    headers = {"Authorization": f"Bearer {key}", "Idempotency-Key": "alert-score-1"}
    response = client.post(
        "/v1/transactions/score", json=high_risk_payload("txn_alert_1"), headers=headers
    )

    assert response.status_code == 200
    alerts = session.scalars(select(Alert).where(Alert.tenant_id == tenant.id)).all()
    assert len(alerts) == 1
    alert_id = str(alerts[0].id)
    listed = client.get("/v1/alerts", headers={"Authorization": f"Bearer {key}"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == alert_id

    detail = client.get(f"/v1/alerts/{alert_id}", headers={"Authorization": f"Bearer {key}"})
    assert detail.status_code == 200
    assert detail.json()["transaction_id"] == "txn_alert_1"
    assert detail.json()["status"] == "open"


def test_alert_lifecycle_notes_and_audit(alert_client: AlertFixture) -> None:
    client, key, session, tenant = alert_client
    score = client.post(
        "/v1/transactions/score",
        json=high_risk_payload("txn_alert_lifecycle"),
        headers={"Authorization": f"Bearer {key}", "Idempotency-Key": "alert-lifecycle-1"},
    )
    alert = session.scalar(select(Alert).where(Alert.tenant_id == tenant.id))
    assert alert is not None
    alert_id = str(alert.id)

    updated = client.patch(
        f"/v1/alerts/{alert_id}",
        json={"status": "in_review", "assigned_to": "analyst-demo", "disposition": "needs_review"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert score.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_review"
    assert updated.json()["assigned_to"] == "analyst-demo"

    note = client.post(
        f"/v1/alerts/{alert_id}/notes",
        json={"body": "Synthetic burst reviewed."},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert note.status_code == 201
    assert note.json()["body"] == "Synthetic burst reviewed."

    resolved = client.patch(
        f"/v1/alerts/{alert_id}",
        json={"status": "resolved", "disposition": "confirmed_risk"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["closed_at"] is not None
    audit_actions = session.scalars(
        select(AuditEvent.action).where(AuditEvent.tenant_id == tenant.id)
    ).all()
    assert "alert.created" in audit_actions
    assert "alert.status_changed" in audit_actions
    assert "case_note.created" in audit_actions


def test_invalid_alert_transition_is_rejected(alert_client: AlertFixture) -> None:
    client, key, session, _tenant = alert_client
    client.post(
        "/v1/transactions/score",
        json=high_risk_payload("txn_alert_invalid_transition"),
        headers={"Authorization": f"Bearer {key}", "Idempotency-Key": "alert-invalid-1"},
    )
    alert = session.scalar(select(Alert))
    assert alert is not None
    alert_id = str(alert.id)
    client.patch(
        f"/v1/alerts/{alert_id}",
        json={"status": "resolved"},
        headers={"Authorization": f"Bearer {key}"},
    )
    response = client.patch(
        f"/v1/alerts/{alert_id}",
        json={"status": "in_review"},
        headers={"Authorization": f"Bearer {key}"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_ALERT_TRANSITION"
