"""Asynchronous event ingestion schemas."""

from pydantic import BaseModel, Field

from app.schemas.transactions import CanonicalTransaction


class EventIngestRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    transaction: CanonicalTransaction


class EventIngestResponse(BaseModel):
    event_id: str
    status: str
    request_id: str
