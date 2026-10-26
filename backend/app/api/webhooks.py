"""Webhook endpoint and delivery management."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.webhook import WebhookDelivery, WebhookEndpoint
from app.schemas.webhooks import (
    WebhookDeliveryResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
)
from app.services.audit import record_audit
from app.services.auth import Principal, require_scope
from app.services.webhooks import create_endpoint, replay_delivery

router = APIRouter(prefix="/v1", tags=["webhooks"])


@router.post("/webhook-endpoints", response_model=WebhookEndpointResponse, status_code=201)
def register_webhook_endpoint(
    endpoint_input: WebhookEndpointCreate,
    request: Request,
    principal: Principal = Depends(require_scope("config:write")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> WebhookEndpointResponse:
    endpoint, secret = create_endpoint(
        session,
        principal.tenant_id,
        endpoint_input.url,
        endpoint_input.secret,
        endpoint_input.subscriptions,
        settings,
    )
    record_audit(
        session,
        tenant_id=principal.tenant_id,
        actor_type="api_key",
        actor_id=str(principal.api_key_id),
        action="webhook_endpoint.created",
        target_type="webhook_endpoint",
        target_id=str(endpoint.id),
        request_id=request.state.request_id,
        details={
            "url_host": endpoint_input.url.split("/", 3)[2],
            "subscriptions": endpoint.subscriptions,
        },
    )
    session.commit()
    return WebhookEndpointResponse(
        id=str(endpoint.id),
        url=endpoint.url,
        subscriptions=endpoint.subscriptions,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at,
        secret=secret,
    )


@router.get("/webhook-endpoints", response_model=list[WebhookEndpointResponse])
def list_webhook_endpoints(
    principal: Principal = Depends(require_scope("config:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> list[WebhookEndpointResponse]:
    endpoints = session.scalars(
        select(WebhookEndpoint)
        .where(WebhookEndpoint.tenant_id == principal.tenant_id)
        .order_by(WebhookEndpoint.created_at.desc())
    ).all()
    return [
        WebhookEndpointResponse(
            id=str(endpoint.id),
            url=endpoint.url,
            subscriptions=endpoint.subscriptions,
            is_active=endpoint.is_active,
            created_at=endpoint.created_at,
        )
        for endpoint in endpoints
    ]


@router.get("/webhook-deliveries", response_model=list[WebhookDeliveryResponse])
def list_webhook_deliveries(
    principal: Principal = Depends(require_scope("config:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> list[WebhookDeliveryResponse]:
    deliveries = session.scalars(
        select(WebhookDelivery)
        .where(WebhookDelivery.tenant_id == principal.tenant_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(100)
    ).all()
    return [
        WebhookDeliveryResponse(
            id=str(delivery.id),
            endpoint_id=str(delivery.endpoint_id),
            event_id=delivery.event_id,
            event_type=delivery.event_type,
            status=delivery.status,
            attempt_count=delivery.attempt_count,
            last_status_code=delivery.last_status_code,
            next_attempt_at=delivery.next_attempt_at,
            delivered_at=delivery.delivered_at,
        )
        for delivery in deliveries
    ]


@router.post("/webhook-deliveries/{delivery_id}/replay", response_model=WebhookDeliveryResponse)
def replay_webhook_delivery(
    delivery_id: UUID,
    request: Request,
    principal: Principal = Depends(require_scope("config:write")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> WebhookDeliveryResponse:
    delivery = session.scalar(
        select(WebhookDelivery).where(
            WebhookDelivery.id == delivery_id,
            WebhookDelivery.tenant_id == principal.tenant_id,
        )
    )
    if delivery is None:
        raise AppError("WEBHOOK_DELIVERY_NOT_FOUND", "Webhook delivery was not found.", 404)
    replay_delivery(session, delivery)
    record_audit(
        session,
        tenant_id=principal.tenant_id,
        actor_type="api_key",
        actor_id=str(principal.api_key_id),
        action="webhook_delivery.replayed",
        target_type="webhook_delivery",
        target_id=str(delivery.id),
        request_id=request.state.request_id,
        details={"event_type": delivery.event_type},
    )
    session.commit()
    return WebhookDeliveryResponse(
        id=str(delivery.id),
        endpoint_id=str(delivery.endpoint_id),
        event_id=delivery.event_id,
        event_type=delivery.event_type,
        status=delivery.status,
        attempt_count=delivery.attempt_count,
        last_status_code=delivery.last_status_code,
        next_attempt_at=delivery.next_attempt_at,
        delivered_at=delivery.delivered_at,
    )
