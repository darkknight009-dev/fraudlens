"""Append-only redacted audit recording."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def record_audit(
    session: Session,
    *,
    tenant_id: UUID | None,
    actor_type: str,
    actor_id: str | None,
    action: str,
    target_type: str,
    target_id: str | None,
    request_id: str | None,
    details: dict[str, object] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        details_redacted=details or {},
    )
    session.add(event)
    return event
