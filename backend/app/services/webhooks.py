"""Signed asynchronous webhook enqueue, delivery, retry, and replay services."""

import hashlib
import hmac
import ipaddress
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from uuid import UUID, uuid4

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models.webhook import WebhookDelivery, WebhookEndpoint


def validate_webhook_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise AppError("INVALID_WEBHOOK_URL", "Webhook URL must be an HTTPS host URL.", 422)
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private or address.is_loopback or address.is_link_local or address.is_reserved
    ):
        raise AppError(
            "INVALID_WEBHOOK_URL", "Private and local webhook destinations are not allowed.", 422
        )
    return url


class WebhookSecretBox:
    def __init__(self, settings: Settings) -> None:
        if not settings.webhook_encryption_key:
            raise AppError(
                "WEBHOOK_SECRET_UNAVAILABLE", "Webhook encryption is not configured.", 503
            )
        try:
            self._fernet = Fernet(settings.webhook_encryption_key.encode())
        except ValueError as exc:
            raise AppError(
                "WEBHOOK_SECRET_UNAVAILABLE", "Webhook encryption is misconfigured.", 503
            ) from exc

    def encrypt(self, secret: str) -> str:
        return self._fernet.encrypt(secret.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        try:
            return self._fernet.decrypt(encrypted.encode()).decode()
        except InvalidToken as exc:
            raise AppError(
                "WEBHOOK_SECRET_UNAVAILABLE", "Webhook secret could not be decrypted.", 503
            ) from exc


def create_endpoint(
    session: Session,
    tenant_id: UUID,
    url: str,
    secret: str,
    subscriptions: list[str],
    settings: Settings,
) -> tuple[WebhookEndpoint, str]:
    validate_webhook_url(url)
    if not secret or len(secret) < 32:
        raise AppError(
            "INVALID_WEBHOOK_SECRET", "Webhook secret must contain at least 32 characters.", 422
        )
    if not subscriptions or any(len(event_type) > 128 for event_type in subscriptions):
        raise AppError(
            "INVALID_WEBHOOK_SUBSCRIPTIONS", "At least one bounded subscription is required.", 422
        )
    box = WebhookSecretBox(settings)
    endpoint = WebhookEndpoint(
        tenant_id=tenant_id,
        url=url,
        secret_encrypted=box.encrypt(secret),
        subscriptions=sorted(set(subscriptions)),
        is_active=True,
    )
    session.add(endpoint)
    session.commit()
    return endpoint, secret


def enqueue_event(
    session: Session,
    tenant_id: UUID,
    event_type: str,
    payload: dict[str, object],
    *,
    event_id: str | None = None,
) -> int:
    event_id = event_id or f"evt_{uuid4().hex}"
    endpoints = session.scalars(
        select(WebhookEndpoint).where(
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.is_active.is_(True),
        )
    ).all()
    created = 0
    for endpoint in endpoints:
        if event_type not in endpoint.subscriptions and "*" not in endpoint.subscriptions:
            continue
        exists = session.scalar(
            select(WebhookDelivery).where(
                WebhookDelivery.tenant_id == tenant_id,
                WebhookDelivery.event_id == event_id,
            )
        )
        if exists is not None:
            continue
        session.add(
            WebhookDelivery(
                tenant_id=tenant_id,
                endpoint_id=endpoint.id,
                event_id=event_id,
                event_type=event_type,
                payload=payload,
                status="pending",
                next_attempt_at=datetime.now(UTC),
            )
        )
        created += 1
    session.flush()
    return created


def signed_headers(
    event_id: str, event_type: str, payload: dict[str, object], secret: str, timestamp: int
) -> dict[str, str]:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = f"{timestamp}.{event_id}.{event_type}.{body}".encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-FraudLens-Event-ID": event_id,
        "X-FraudLens-Event-Type": event_type,
        "X-FraudLens-Timestamp": str(timestamp),
        "X-FraudLens-Signature": f"sha256={signature}",
    }


def dispatch_delivery(
    session: Session,
    delivery: WebhookDelivery,
    endpoint: WebhookEndpoint,
    settings: Settings,
    *,
    client: httpx.Client | None = None,
) -> WebhookDelivery:
    validate_webhook_url(endpoint.url)
    secret = WebhookSecretBox(settings).decrypt(endpoint.secret_encrypted)
    now = datetime.now(UTC)
    delivery.attempt_count += 1
    headers = signed_headers(
        delivery.event_id, delivery.event_type, delivery.payload, secret, int(now.timestamp())
    )
    owns_client = client is None
    sender = client or httpx.Client(
        timeout=settings.webhook_timeout_seconds, follow_redirects=False
    )
    try:
        response = sender.post(endpoint.url, json=delivery.payload, headers=headers)
        delivery.last_status_code = response.status_code
        if 200 <= response.status_code < 300:
            delivery.status = "delivered"
            delivery.delivered_at = now
            delivery.next_attempt_at = None
            delivery.last_error = None
        elif delivery.attempt_count >= settings.webhook_max_attempts:
            delivery.status = "dead_letter"
            delivery.last_error = "destination returned a non-success status"
        else:
            delivery.status = "retrying"
            delivery.next_attempt_at = now + timedelta(
                seconds=min(3_600, 2**delivery.attempt_count)
            )
            delivery.last_error = "destination returned a non-success status"
    except httpx.HTTPError:
        delivery.last_error = "destination request failed"
        if delivery.attempt_count >= settings.webhook_max_attempts:
            delivery.status = "dead_letter"
        else:
            delivery.status = "retrying"
            delivery.next_attempt_at = now + timedelta(
                seconds=min(3_600, 2**delivery.attempt_count)
            )
    finally:
        if owns_client:
            sender.close()
    session.commit()
    return delivery


def replay_delivery(session: Session, delivery: WebhookDelivery) -> WebhookDelivery:
    if delivery.status not in {"dead_letter", "retrying", "failed"}:
        raise AppError(
            "INVALID_WEBHOOK_REPLAY", "Only failed webhook deliveries can be replayed.", 409
        )
    delivery.status = "pending"
    delivery.next_attempt_at = datetime.now(UTC)
    delivery.last_error = None
    session.commit()
    return delivery
