"""Audit API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: str
    actor_type: str
    actor_id: str | None
    action: str
    target_type: str
    target_id: str | None
    request_id: str | None
    details_redacted: dict[str, Any]
    created_at: datetime


class PaginatedAuditEvents(BaseModel):
    items: list[AuditEventResponse]
    limit: int
    offset: int
    total: int
