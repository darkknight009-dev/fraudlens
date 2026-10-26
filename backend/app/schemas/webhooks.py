"""Webhook management API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class WebhookEndpointCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2_048)
    secret: str = Field(min_length=32, max_length=512)
    subscriptions: list[str] = Field(min_length=1, max_length=50)


class WebhookEndpointResponse(BaseModel):
    id: str
    url: str
    subscriptions: list[str]
    is_active: bool
    created_at: datetime
    secret: str | None = None


class WebhookDeliveryResponse(BaseModel):
    id: str
    endpoint_id: str
    event_id: str
    event_type: str
    status: str
    attempt_count: int
    last_status_code: int | None
    next_attempt_at: datetime | None
    delivered_at: datetime | None
