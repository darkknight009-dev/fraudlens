from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import app
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.services.auth import generate_api_key

ScoringFixture = tuple[TestClient, str, Tenant, Session]


def make_settings() -> Settings:
    return Settings(
        app_env="test",
        api_key_hash_pepper="test-pepper-with-at-least-32-characters",
        idempotency_ttl_seconds=86_400,
    )


@pytest.fixture()
def scoring_client(db_session: Session) -> Iterator[tuple[TestClient, str, Tenant, Session]]:
    tenant = Tenant(name="Scoring Tenant")
    db_session.add(tenant)
    db_session.commit()
    generated = generate_api_key(make_settings().api_key_hash_pepper)
    from app.models.api_key import APIKey, APIKeyScope

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

    def override_db() -> Session:
        return db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = make_settings
    try:
        yield TestClient(app), generated.plaintext, tenant, db_session
    finally:
        app.dependency_overrides.clear()


def test_valid_transaction_produces_reproducible_shadow_assessment(
    scoring_client: tuple[TestClient, str, Tenant, Session],
) -> None:
    client, key, tenant, session = scoring_client
    payload = {
        "transaction_id": "txn_normal_1",
        "amount_minor": 2500,
        "currency": "inr",
        "occurred_at": "2026-10-26T15:30:00Z",
        "account_ref": "acct_pseudo_501",
        "device_ref": "device_pseudo_91",
        "merchant_ref": "merchant_demo_1",
        "channel": "upi",
        "provider_status": "pending",
        "metadata": {"source": "merchant_simulator"},
    }

    first = client.post(
        "/v1/transactions/score",
        json=payload,
        headers={"Authorization": f"Bearer {key}", "Idempotency-Key": "score-normal-1"},
    )
    second = client.post(
        "/v1/transactions/score",
        json=payload,
        headers={"Authorization": f"Bearer {key}", "Idempotency-Key": "score-normal-1"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["risk_score"] == 0
    assert first.json()["risk_level"] == "low"
    assert first.json()["mode"] == "shadow"
    assert first.json()["assessment_status"] == "complete"
    assert first.json()["detector_status"] == {"rules": "complete", "ml": "disabled"}
    assert first.json()["request_id"].startswith("req_")
    assert session.query(Transaction).filter(Transaction.tenant_id == tenant.id).count() == 1


def test_rules_create_explainable_bounded_score(scoring_client: ScoringFixture) -> None:
    client, key, _tenant, _session = scoring_client
    payload = {
        "transaction_id": "txn_high_1",
        "amount_minor": 2_000_000,
        "currency": "INR",
        "occurred_at": "2026-10-26T15:30:00Z",
        "account_ref": "acct_risky_1",
        "channel": "card",
        "provider_status": "declined",
    }

    response = client.post(
        "/v1/transactions/score",
        json=payload,
        headers={"Authorization": f"Bearer {key}", "Idempotency-Key": "score-high-1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] == 60
    assert body["risk_level"] == "high"
    assert {signal["reason_code"] for signal in body["signals"]} == {
        "HIGH_TRANSACTION_AMOUNT",
        "PROVIDER_STATUS_RISK",
    }
    assert all(signal["source"] == "rule" for signal in body["signals"])
    assert all("evidence" in signal for signal in body["signals"])
    assert 0 <= body["risk_score"] <= 100


def test_conflicting_idempotency_body_returns_409(scoring_client: ScoringFixture) -> None:
    client, key, _tenant, _session = scoring_client
    base = {
        "transaction_id": "txn_conflict_1",
        "amount_minor": 100,
        "currency": "INR",
        "occurred_at": "2026-10-26T15:30:00Z",
        "account_ref": "acct_conflict_1",
        "channel": "wallet",
    }
    headers = {"Authorization": f"Bearer {key}", "Idempotency-Key": "score-conflict-1"}
    assert client.post("/v1/transactions/score", json=base, headers=headers).status_code == 200

    changed = {**base, "amount_minor": 101}
    response = client.post("/v1/transactions/score", json=changed, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_missing_idempotency_key_is_rejected(scoring_client: ScoringFixture) -> None:
    client, key, _tenant, _session = scoring_client
    payload = {
        "transaction_id": "txn_no_key",
        "amount_minor": 100,
        "currency": "INR",
        "occurred_at": "2026-10-26T15:30:00Z",
        "account_ref": "acct_no_key",
        "channel": "other",
    }

    response = client.post(
        "/v1/transactions/score",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_scoring_requires_authentication(scoring_client: ScoringFixture) -> None:
    client, _key, _tenant, _session = scoring_client
    payload = {
        "transaction_id": "txn_unauthorized",
        "amount_minor": 100,
        "currency": "INR",
        "occurred_at": "2026-10-26T15:30:00Z",
        "account_ref": "acct_unauthorized",
        "channel": "other",
    }

    response = client.post(
        "/v1/transactions/score",
        json=payload,
        headers={"Idempotency-Key": "score-unauthorized-1"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_invalid_sensitive_or_unknown_metadata_is_rejected(scoring_client: ScoringFixture) -> None:
    client, key, _tenant, _session = scoring_client
    payload = {
        "transaction_id": "txn_invalid_metadata",
        "amount_minor": 100,
        "currency": "INR",
        "occurred_at": "2026-10-26T15:30:00Z",
        "account_ref": "acct_invalid",
        "channel": "other",
        "metadata": {"cvv": "123"},
    }

    response = client.post(
        "/v1/transactions/score",
        json=payload,
        headers={"Authorization": f"Bearer {key}", "Idempotency-Key": "score-invalid-1"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_same_transaction_reference_is_tenant_scoped(db_session: Session) -> None:
    tenant_a = Tenant(name="A")
    tenant_b = Tenant(name="B")
    db_session.add_all([tenant_a, tenant_b])
    db_session.commit()
    transaction_a = Transaction(
        tenant_id=tenant_a.id,
        external_transaction_id="same-ref",
        amount_minor=10,
        currency="INR",
        occurred_at=datetime.now(UTC),
        account_ref_hash="a" * 64,
        channel="other",
        safe_metadata={},
    )
    transaction_b = Transaction(
        tenant_id=tenant_b.id,
        external_transaction_id="same-ref",
        amount_minor=20,
        currency="INR",
        occurred_at=datetime.now(UTC),
        account_ref_hash="b" * 64,
        channel="other",
        safe_metadata={},
    )
    db_session.add_all([transaction_a, transaction_b])
    db_session.commit()

    stored_a = db_session.scalar(select(Transaction).where(Transaction.tenant_id == tenant_a.id))
    stored_b = db_session.scalar(select(Transaction).where(Transaction.tenant_id == tenant_b.id))
    assert stored_a is not None and stored_a.amount_minor == 10
    assert stored_b is not None and stored_b.amount_minor == 20
