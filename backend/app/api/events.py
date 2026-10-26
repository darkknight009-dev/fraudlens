"""Durable asynchronous event ingestion endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import EventInbox
from app.schemas.events import EventIngestRequest, EventIngestResponse
from app.services.auth import Principal, require_scope

router = APIRouter(prefix="/v1/events", tags=["events"])


@router.post("", response_model=EventIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_event(
    event: EventIngestRequest,
    request: Request,
    principal: Principal = Depends(require_scope("transactions:score")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> EventIngestResponse:
    existing = session.scalar(
        select(EventInbox).where(
            EventInbox.tenant_id == principal.tenant_id,
            EventInbox.event_id == event.event_id,
        )
    )
    if existing is not None:
        return EventIngestResponse(
            event_id=existing.event_id,
            status=existing.status,
            request_id=request.state.request_id,
        )
    inbox = EventInbox(
        tenant_id=principal.tenant_id,
        api_key_id=principal.api_key_id,
        event_id=event.event_id,
        payload=event.transaction.model_dump(mode="json"),
        status="pending",
        created_at=datetime.now(UTC),
    )
    session.add(inbox)
    session.commit()
    return EventIngestResponse(
        event_id=event.event_id, status="pending", request_id=request.state.request_id
    )
