"""Alert and investigation API schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AlertStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class AlertUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AlertStatus | None = None
    assigned_to: str | None = Field(default=None, max_length=200)
    disposition: str | None = Field(default=None, max_length=100)


class CaseNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4_000)


class CaseNoteResponse(BaseModel):
    id: str
    author_id: str | None
    body: str
    created_at: datetime


class AlertResponse(BaseModel):
    id: str
    tenant_id: str
    assessment_id: str
    transaction_id: str
    status: AlertStatus
    priority: int
    assigned_to: str | None
    disposition: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    assessment: dict[str, Any] | None = None
    notes: list[CaseNoteResponse] = Field(default_factory=list)


class PaginatedAlerts(BaseModel):
    items: list[AlertResponse]
    limit: int
    offset: int
    total: int
