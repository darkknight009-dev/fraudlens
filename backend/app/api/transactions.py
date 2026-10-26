"""Versioned transaction scoring endpoints."""

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.assessment import Assessment, RiskSignal
from app.models.transaction import Transaction
from app.schemas.scoring import (
    AssessmentList,
    AssessmentStatus,
    DetectorStatus,
    RiskLevel,
    RiskSignalResponse,
    ScoreResponse,
    SignalSeverity,
    SignalSource,
)
from app.schemas.transactions import CanonicalTransaction
from app.services.auth import Principal, require_scope
from app.services.scoring import score_transaction

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])


def _assessment_response(
    session: Session, assessment: Assessment, transaction_id: str
) -> ScoreResponse:
    signals = session.scalars(
        select(RiskSignal).where(
            RiskSignal.assessment_id == assessment.id,
            RiskSignal.tenant_id == assessment.tenant_id,
        )
    ).all()
    return ScoreResponse(
        assessment_id=f"assess_{assessment.id.hex}",
        transaction_id=transaction_id,
        risk_score=assessment.risk_score,
        risk_level=RiskLevel(assessment.risk_level),
        mode=assessment.mode,
        assessment_status=AssessmentStatus(assessment.assessment_status),
        signals=[
            RiskSignalResponse(
                reason_code=signal.reason_code,
                message=signal.message_template_key,
                source=SignalSource(signal.source),
                severity=SignalSeverity(signal.severity),
                evidence=signal.evidence,
                contribution=signal.contribution or 0,
            )
            for signal in signals
        ],
        detector_status=DetectorStatus.model_validate(assessment.detector_status),
        rule_set_version=assessment.rule_set_version,
        model_version=assessment.model_version,
        request_id=assessment.request_id,
    )


@router.post("/score", response_model=ScoreResponse)
def score(
    transaction: CanonicalTransaction,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(require_scope("transactions:score")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ScoreResponse:
    """Return a deterministic advisory assessment for a canonical transaction."""

    return score_transaction(
        session=session,
        principal=principal,
        transaction_input=transaction,
        request_id=request.state.request_id,
        idempotency_key=idempotency_key,
        settings=settings,
    )


@router.get("/{transaction_id}/assessments", response_model=AssessmentList)
def list_transaction_assessments(
    transaction_id: str = Path(max_length=128),
    principal: Principal = Depends(require_scope("transactions:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AssessmentList:
    transaction = session.scalar(
        select(Transaction).where(
            Transaction.tenant_id == principal.tenant_id,
            Transaction.external_transaction_id == transaction_id,
        )
    )
    if transaction is None:
        from app.core.errors import AppError

        raise AppError("TRANSACTION_NOT_FOUND", "Transaction was not found.", 404)
    query = select(Assessment).where(
        Assessment.tenant_id == principal.tenant_id,
        Assessment.transaction_id == transaction.id,
    )
    assessments = list(
        session.scalars(
            query.order_by(Assessment.created_at.desc(), Assessment.id).limit(limit).offset(offset)
        ).all()
    )
    total = (
        session.scalar(
            select(func.count(Assessment.id)).where(
                Assessment.tenant_id == principal.tenant_id,
                Assessment.transaction_id == transaction.id,
            )
        )
        or 0
    )
    return AssessmentList(
        items=[
            _assessment_response(session, assessment, transaction_id) for assessment in assessments
        ],
        limit=limit,
        offset=offset,
        total=total,
    )
