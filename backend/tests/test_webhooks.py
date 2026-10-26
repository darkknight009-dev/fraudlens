import httpx
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models.tenant import Tenant
from app.models.webhook import WebhookDelivery
from app.services.webhooks import (
    WebhookSecretBox,
    create_endpoint,
    dispatch_delivery,
    enqueue_event,
    signed_headers,
    validate_webhook_url,
)


def webhook_settings() -> Settings:
    return Settings(
        app_env="test",
        api_key_hash_pepper="test-pepper-with-at-least-32-characters",
        webhook_encryption_key=Fernet.generate_key().decode(),
        webhook_max_attempts=2,
    )


def test_webhook_url_rejects_private_destinations() -> None:
    with pytest.raises(AppError):
        validate_webhook_url("http://127.0.0.1:8080/hook")
    with pytest.raises(AppError):
        validate_webhook_url("https://127.0.0.1:8080/hook")


def test_secret_is_encrypted_and_event_is_idempotently_enqueued(db_session: Session) -> None:
    tenant = Tenant(name="Webhook Tenant")
    db_session.add(tenant)
    db_session.commit()
    settings = webhook_settings()
    endpoint, _ = create_endpoint(
        db_session,
        tenant.id,
        "https://example.com/fraudlens",
        "s" * 40,
        ["alert.created"],
        settings,
    )
    assert endpoint.secret_encrypted != "s" * 40
    assert WebhookSecretBox(settings).decrypt(endpoint.secret_encrypted) == "s" * 40
    payload: dict[str, object] = {"alert_id": "alert_1", "risk_level": "high"}
    assert (
        enqueue_event(db_session, tenant.id, "alert.created", dict(payload), event_id="event_1")
        == 1
    )
    assert (
        enqueue_event(db_session, tenant.id, "alert.created", dict(payload), event_id="event_1")
        == 0
    )
    delivery = db_session.scalar(select(WebhookDelivery))
    assert delivery is not None
    assert delivery.event_id == "event_1"


def test_signature_is_deterministic() -> None:
    headers = signed_headers("event_1", "alert.created", {"alert_id": "a"}, "s" * 40, 1_700_000_000)

    assert headers["X-FraudLens-Signature"].startswith("sha256=")
    assert headers["X-FraudLens-Timestamp"] == "1700000000"


def test_delivery_marks_success_or_dead_letter(db_session: Session) -> None:
    tenant = Tenant(name="Webhook Tenant")
    db_session.add(tenant)
    db_session.commit()
    settings = webhook_settings()
    endpoint, _ = create_endpoint(
        db_session,
        tenant.id,
        "https://example.com/fraudlens",
        "s" * 40,
        ["alert.created"],
        settings,
    )
    enqueue_event(
        db_session, tenant.id, "alert.created", {"alert_id": "a"}, event_id="event_success"
    )
    delivery = db_session.scalar(select(WebhookDelivery))
    assert delivery is not None

    success_client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(204)))
    dispatch_delivery(db_session, delivery, endpoint, settings, client=success_client)
    assert delivery.status == "delivered"
    success_client.close()

    enqueue_event(
        db_session, tenant.id, "alert.created", {"alert_id": "b"}, event_id="event_failure"
    )
    failed = db_session.scalar(
        select(WebhookDelivery).where(WebhookDelivery.event_id == "event_failure")
    )
    assert failed is not None
    settings.webhook_max_attempts = 1
    failure_client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500)))
    dispatch_delivery(db_session, failed, endpoint, settings, client=failure_client)
    assert failed.status == "dead_letter"
    failure_client.close()
