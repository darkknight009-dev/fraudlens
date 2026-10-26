"""Tenant-scoped alert lifecycle and deduplication."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.alert import Alert, CaseNote
from app.models.assessment import Assessment
from app.services.audit import record_audit
from app.services.webhooks import enqueue_event

VALID_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_review", "escalated", "false_positive", "resolved"},
    "in_review": {"open", "escalated", "false_positive", "resolved"},
    "escalated": {"in_review", "resolved", "false_positive"},
    "resolved": set(),
    "false_positive": set(),
}


def create_alert_if_needed(
    session: Session, assessment: Assessment, *, request_id: str
) -> Alert | None:
    """Create at most one alert per assessment when the default high-risk threshold is met."""

    if assessment.risk_score < 60:
        return None
    existing = session.scalar(
        select(Alert).where(
            Alert.tenant_id == assessment.tenant_id,
            Alert.assessment_id == assessment.id,
        )
    )
    if existing is not None:
        return existing
    alert = Alert(
        tenant_id=assessment.tenant_id,
        assessment_id=assessment.id,
        status="open",
        priority=assessment.risk_score,
    )
    session.add(alert)
    session.flush()
    record_audit(
        session,
        tenant_id=assessment.tenant_id,
        actor_type="system",
        actor_id="scoring",
        action="alert.created",
        target_type="alert",
        target_id=str(alert.id),
        request_id=request_id,
        details={"priority": alert.priority, "risk_level": assessment.risk_level},
    )
    enqueue_event(
        session,
        assessment.tenant_id,
        "alert.created",
        {
            "event_id": f"alert.created:{alert.id}",
            "alert_id": str(alert.id),
            "assessment_id": str(assessment.id),
            "risk_level": assessment.risk_level,
        },
        event_id=f"alert.created:{alert.id}",
    )
    return alert


def get_alert(session: Session, tenant_id: UUID, alert_id: UUID) -> Alert:
    alert = session.scalar(select(Alert).where(Alert.id == alert_id, Alert.tenant_id == tenant_id))
    if alert is None:
        raise AppError("ALERT_NOT_FOUND", "Alert was not found.", 404)
    return alert


def list_alerts(
    session: Session, tenant_id: UUID, limit: int, offset: int, status: str | None
) -> tuple[list[Alert], int]:
    query = select(Alert).where(Alert.tenant_id == tenant_id)
    count_query = select(func.count(Alert.id)).where(Alert.tenant_id == tenant_id)
    if status is not None:
        query = query.where(Alert.status == status)
        count_query = count_query.where(Alert.status == status)
    alerts = list(
        session.scalars(
            query.order_by(Alert.created_at.desc(), Alert.id).limit(limit).offset(offset)
        ).all()
    )
    total = session.scalar(count_query) or 0
    return alerts, total


def update_alert(
    session: Session,
    alert: Alert,
    *,
    status: str | None,
    assigned_to: str | None,
    disposition: str | None,
    principal_id: UUID,
    request_id: str,
) -> Alert:
    if status is not None and status != alert.status:
        if status not in VALID_TRANSITIONS.get(alert.status, set()):
            raise AppError(
                "INVALID_ALERT_TRANSITION", "The alert status transition is invalid.", 409
            )
        previous = alert.status
        alert.status = status
        if status in {"resolved", "false_positive"}:
            alert.closed_at = datetime.now(UTC)
        record_audit(
            session,
            tenant_id=alert.tenant_id,
            actor_type="api_key",
            actor_id=str(principal_id),
            action="alert.status_changed",
            target_type="alert",
            target_id=str(alert.id),
            request_id=request_id,
            details={"from": previous, "to": status},
        )
    if assigned_to is not None:
        alert.assigned_to = assigned_to
        record_audit(
            session,
            tenant_id=alert.tenant_id,
            actor_type="api_key",
            actor_id=str(principal_id),
            action="alert.assigned",
            target_type="alert",
            target_id=str(alert.id),
            request_id=request_id,
            details={"assigned": True},
        )
    if disposition is not None:
        alert.disposition = disposition
        record_audit(
            session,
            tenant_id=alert.tenant_id,
            actor_type="api_key",
            actor_id=str(principal_id),
            action="alert.disposition_recorded",
            target_type="alert",
            target_id=str(alert.id),
            request_id=request_id,
            details={"disposition_set": True},
        )
    session.commit()
    return alert


def add_note(
    session: Session, alert: Alert, body: str, principal_id: UUID, request_id: str
) -> CaseNote:
    note = CaseNote(
        tenant_id=alert.tenant_id,
        case_id=alert.id,
        author_id=str(principal_id),
        body=body,
    )
    session.add(note)
    record_audit(
        session,
        tenant_id=alert.tenant_id,
        actor_type="api_key",
        actor_id=str(principal_id),
        action="case_note.created",
        target_type="alert",
        target_id=str(alert.id),
        request_id=request_id,
        details={"body_length": len(body)},
    )
    session.commit()
    return note
