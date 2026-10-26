from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import app
from app.models.api_key import APIKey, APIKeyScope
from app.models.payment import PaymentIntent
from app.models.tenant import Tenant
from app.services.auth import generate_api_key


def payment_settings() -> Settings:
    return Settings(
        app_env="test",
        api_key_hash_pepper="test-pepper-with-at-least-32-characters",
        idempotency_ttl_seconds=86_400,
    )


def payment_client(db_session: Session) -> Iterator[tuple[TestClient, str, Session, Tenant]]:
    tenant = Tenant(name="Payment Tenant")
    db_session.add(tenant)
    db_session.commit()
    generated = generate_api_key(payment_settings().api_key_hash_pepper)
    db_session.add(
        APIKey(
            tenant_id=tenant.id,
            key_prefix=generated.prefix,
            key_hash=generated.digest,
            created_by="test",
            scopes=[
                APIKeyScope(scope="transactions:score"),
                APIKeyScope(scope="transactions:read"),
                APIKeyScope(scope="cases:read"),
                APIKeyScope(scope="cases:write"),
            ],
        )
    )
    db_session.commit()

    def override_db() -> Session:
        return db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = payment_settings
    try:
        yield TestClient(app), generated.plaintext, db_session, tenant
    finally:
        app.dependency_overrides.clear()


PaymentFixture = tuple[TestClient, str, Session, Tenant]


def payment_payload(order_id: str = "order_001") -> dict[str, object]:
    return {
        "merchant_order_id": order_id,
        "amount_minor": 2_000_000,
        "currency": "INR",
        "account_ref": "acct_checkout_001",
        "device_ref": "device_checkout_001",
        "merchant_ref": "merchant_demo",
        "channel": "upi",
        "payment_method": "test_approved",
        "metadata": {"source": "sandbox_checkout"},
    }


def test_sandbox_payment_runs_gateway_and_fraudlens_workflow(
    db_session: Session,
) -> None:
    fixture = payment_client(db_session)
    client, key, session, tenant = next(fixture)
    try:
        response = client.post(
            "/v1/sandbox/payments",
            json=payment_payload(),
            headers={"Authorization": f"Bearer {key}", "Idempotency-Key": "payment_001"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["payment_status"] == "succeeded"
        assert body["provider_status"] == "approved"
        assert body["risk_score"] == 35
        assert body["risk_recommendation"] == "monitor"
        assert [step["name"] for step in body["timeline"]] == [
            "checkout_received",
            "mock_gateway",
            "fraudlens_assessment",
            "merchant_policy",
            "payment_outcome",
        ]
        assert (
            session.scalar(select(PaymentIntent).where(PaymentIntent.tenant_id == tenant.id))
            is not None
        )
    finally:
        app.dependency_overrides.clear()


def test_sandbox_payment_idempotency_and_declined_provider(db_session: Session) -> None:
    fixture = payment_client(db_session)
    client, key, _session, _tenant = next(fixture)
    try:
        headers = {"Authorization": f"Bearer {key}", "Idempotency-Key": "payment_002"}
        payload = payment_payload("order_002")
        payload["payment_method"] = "test_declined"
        first = client.post("/v1/sandbox/payments", json=payload, headers=headers)
        duplicate = client.post("/v1/sandbox/payments", json=payload, headers=headers)
        assert first.status_code == 201
        assert duplicate.status_code == 201
        assert first.json() == duplicate.json()
        assert first.json()["payment_status"] == "failed"
        assert first.json()["provider_status"] == "declined"
    finally:
        app.dependency_overrides.clear()


def test_sandbox_payment_requires_authentication(db_session: Session) -> None:
    fixture = payment_client(db_session)
    client, _key, _session, _tenant = next(fixture)
    try:
        response = client.post(
            "/v1/sandbox/payments",
            json=payment_payload("order_unauthorized"),
            headers={"Idempotency-Key": "payment_unauthorized"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
