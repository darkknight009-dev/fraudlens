from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import app
from app.models.api_key import APIKey, APIKeyScope
from app.models.event import EventInbox
from app.models.tenant import Tenant
from app.services.auth import generate_api_key


def event_settings() -> Settings:
    return Settings(app_env="test", api_key_hash_pepper="test-pepper-with-at-least-32-characters")


def test_event_ingestion_is_durable_and_idempotent(db_session: Session) -> None:
    tenant = Tenant(name="Event Tenant")
    db_session.add(tenant)
    db_session.commit()
    generated = generate_api_key(event_settings().api_key_hash_pepper)
    db_session.add(
        APIKey(
            tenant_id=tenant.id,
            key_prefix=generated.prefix,
            key_hash=generated.digest,
            created_by="test",
            scopes=[APIKeyScope(scope="transactions:score")],
        )
    )
    db_session.commit()

    def override_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = event_settings
    try:
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {generated.plaintext}"}
        payload = {
            "event_id": "event_txn_1",
            "transaction": {
                "transaction_id": "txn_event_1",
                "amount_minor": 100,
                "currency": "INR",
                "occurred_at": "2026-10-26T15:30:00Z",
                "account_ref": "acct_event_1",
                "channel": "upi",
            },
        }
        first = client.post("/v1/events", json=payload, headers=headers)
        second = client.post("/v1/events", json=payload, headers=headers)
        assert first.status_code == 202
        assert second.status_code == 202
        assert first.json()["event_id"] == second.json()["event_id"] == "event_txn_1"
        assert (
            db_session.scalar(select(EventInbox).where(EventInbox.tenant_id == tenant.id))
            is not None
        )
        assert db_session.query(EventInbox).filter(EventInbox.tenant_id == tenant.id).count() == 1
    finally:
        app.dependency_overrides.clear()
