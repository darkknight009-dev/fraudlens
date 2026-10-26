"""Tenant-scoped alert and case investigation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models.alert import Alert, CaseNote
from app.models.assessment import Assessment
from app.models.transaction import Transaction
from app.schemas.alerts import (
    AlertResponse,
    AlertStatus,
    AlertUpdate,
    CaseNoteCreate,
    CaseNoteResponse,
    PaginatedAlerts,
)
from app.services.alerts import add_note, get_alert, list_alerts, update_alert
from app.services.auth import Principal, require_scope

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


def _to_response(session: Session, alert: Alert) -> AlertResponse:
    assessment = session.scalar(
        select(Assessment).where(
            Assessment.id == alert.assessment_id,
            Assessment.tenant_id == alert.tenant_id,
        )
    )
    if assessment is None:
        raise AppError("ASSESSMENT_NOT_FOUND", "The linked assessment was not found.", 500)
    transaction = session.scalar(
        select(Transaction).where(
            Transaction.id == assessment.transaction_id,
            Transaction.tenant_id == alert.tenant_id,
        )
    )
    if transaction is None:
        raise AppError("TRANSACTION_NOT_FOUND", "The linked transaction was not found.", 500)
    notes = session.scalars(
        select(CaseNote)
        .where(CaseNote.case_id == alert.id, CaseNote.tenant_id == alert.tenant_id)
        .order_by(CaseNote.created_at)
    ).all()
    return AlertResponse(
        id=str(alert.id),
        tenant_id=str(alert.tenant_id),
        assessment_id=str(alert.assessment_id),
        transaction_id=transaction.external_transaction_id,
        status=AlertStatus(alert.status),
        priority=alert.priority,
        assigned_to=alert.assigned_to,
        disposition=alert.disposition,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        closed_at=alert.closed_at,
        assessment={"risk_score": assessment.risk_score, "risk_level": assessment.risk_level},
        notes=[
            CaseNoteResponse(
                id=str(note.id),
                author_id=note.author_id,
                body=note.body,
                created_at=note.created_at,
            )
            for note in notes
        ],
    )


@router.get("", response_model=PaginatedAlerts)
def list_alerts_endpoint(
    principal: Principal = Depends(require_scope("cases:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
) -> PaginatedAlerts:
    alerts, total = list_alerts(session, principal.tenant_id, limit, offset, status)
    return PaginatedAlerts(
        items=[_to_response(session, alert) for alert in alerts],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_endpoint(
    alert_id: UUID,
    principal: Principal = Depends(require_scope("cases:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> AlertResponse:
    return _to_response(session, get_alert(session, principal.tenant_id, alert_id))


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert_endpoint(
    alert_id: UUID,
    update: AlertUpdate,
    request: Request,
    principal: Principal = Depends(require_scope("cases:write")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> AlertResponse:
    alert = get_alert(session, principal.tenant_id, alert_id)
    updated = update_alert(
        session,
        alert,
        status=update.status.value if update.status is not None else None,
        assigned_to=update.assigned_to,
        disposition=update.disposition,
        principal_id=principal.api_key_id,
        request_id=request.state.request_id,
    )
    return _to_response(session, updated)


@router.post("/{alert_id}/notes", response_model=CaseNoteResponse, status_code=201)
def add_alert_note(
    alert_id: UUID,
    note_input: CaseNoteCreate,
    request: Request,
    principal: Principal = Depends(require_scope("cases:write")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> CaseNoteResponse:
    alert = get_alert(session, principal.tenant_id, alert_id)
    note = add_note(session, alert, note_input.body, principal.api_key_id, request.state.request_id)
    return CaseNoteResponse(
        id=str(note.id), author_id=note.author_id, body=note.body, created_at=note.created_at
    )
