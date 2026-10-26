"""Tenant-scoped audit event reads."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventResponse, PaginatedAuditEvents
from app.services.auth import Principal, require_scope

router = APIRouter(prefix="/v1/audit-events", tags=["audit"])


@router.get("", response_model=PaginatedAuditEvents)
def list_audit_events(
    principal: Principal = Depends(require_scope("audit:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedAuditEvents:
    events = list(
        session.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == principal.tenant_id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id)
            .limit(limit)
            .offset(offset)
        ).all()
    )
    total = (
        session.scalar(
            select(func.count(AuditEvent.id)).where(AuditEvent.tenant_id == principal.tenant_id)
        )
        or 0
    )
    return PaginatedAuditEvents(
        items=[
            AuditEventResponse(
                id=str(event.id),
                actor_type=event.actor_type,
                actor_id=event.actor_id,
                action=event.action,
                target_type=event.target_type,
                target_id=event.target_id,
                request_id=event.request_id,
                details_redacted=event.details_redacted,
                created_at=event.created_at,
            )
            for event in events
        ],
        limit=limit,
        offset=offset,
        total=total,
    )
