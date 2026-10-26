"""End-to-end synthetic checkout orchestration.

This models the integration boundary without collecting payment credentials or
calling a real provider. The mock provider result remains the payment outcome;
FraudLens produces a separate advisory risk recommendation.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models.assessment import Assessment
from app.models.idempotency import IdempotencyRecord
from app.models.payment import PaymentAttempt, PaymentIntent
from app.models.transaction import Transaction
from app.schemas.payments import (
    PaymentAttemptResponse,
    PaymentCreate,
    PaymentList,
    PaymentResponse,
    PaymentTimelineStep,
    TestPaymentMethod,
)
from app.schemas.transactions import CanonicalTransaction
from app.services.audit import record_audit
from app.services.auth import Principal
from app.services.scoring import score_transaction

PAYMENT_ENDPOINT = "/v1/sandbox/payments"


def _fingerprint(request: PaymentCreate) -> str:
    body = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


def _validate_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise AppError("IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key is required.", 400)
    value = value.strip()
    if len(value) > 255 or any(ord(character) < 33 or ord(character) > 126 for character in value):
        raise AppError("INVALID_IDEMPOTENCY_KEY", "Idempotency-Key is invalid.", 400)
    return value


def mock_gateway_authorize(
    payment: PaymentCreate,
) -> tuple[str, str, str, dict[str, str | int | bool]]:
    """Return a deterministic provider result for the showcase checkout."""

    provider_reference = f"mock_{uuid4().hex[:20]}"
    if payment.payment_method is TestPaymentMethod.DECLINED:
        return (
            "declined",
            "failed",
            provider_reference,
            {"test_scenario": "declined", "network": "sandbox"},
        )
    if payment.payment_method is TestPaymentMethod.TIMEOUT:
        return (
            "timeout",
            "failed",
            provider_reference,
            {"test_scenario": "timeout", "network": "sandbox"},
        )
    return (
        "approved",
        "succeeded",
        provider_reference,
        {"test_scenario": "approved", "network": "sandbox"},
    )


def _timeline(payment: PaymentIntent) -> list[PaymentTimelineStep]:
    return [
        PaymentTimelineStep(
            name="checkout_received",
            status="complete",
            detail="Merchant checkout request accepted.",
        ),
        PaymentTimelineStep(
            name="mock_gateway",
            status="complete" if payment.provider_status != "timeout" else "failed",
            detail=f"Sandbox provider returned {payment.provider_status}.",
        ),
        PaymentTimelineStep(
            name="fraudlens_assessment",
            status="complete" if payment.risk_score is not None else "unavailable",
            detail=(
                f"Shadow assessment scored {payment.risk_score}/100 ({payment.risk_level})."
                if payment.risk_score is not None
                else "No assessment was persisted."
            ),
        ),
        PaymentTimelineStep(
            name="merchant_policy",
            status="complete" if payment.merchant_decision else "pending",
            detail=payment.merchant_decision or "Merchant policy has not returned a decision.",
        ),
        PaymentTimelineStep(
            name="payment_outcome",
            status="complete",
            detail=(
                f"Payment remains {payment.payment_status}; "
                "FraudLens did not change the provider outcome."
            ),
        ),
    ]


def _response(session: Session, payment: PaymentIntent) -> PaymentResponse:
    attempts = session.scalars(
        select(PaymentAttempt)
        .where(
            PaymentAttempt.payment_intent_id == payment.id,
            PaymentAttempt.tenant_id == payment.tenant_id,
        )
        .order_by(PaymentAttempt.created_at)
    ).all()
    return PaymentResponse(
        id=str(payment.id),
        merchant_order_id=payment.merchant_order_id,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        channel=payment.channel,
        payment_method_label=payment.payment_method_label,
        payment_status=payment.payment_status,
        provider_status=payment.provider_status,
        provider_reference=payment.provider_reference,
        risk_score=payment.risk_score,
        risk_level=payment.risk_level,
        risk_recommendation=payment.risk_recommendation,
        assessment_id=f"assess_{payment.assessment_id.hex}" if payment.assessment_id else None,
        transaction_id=(
            session.scalar(
                select(Transaction.external_transaction_id).where(
                    Transaction.id == payment.transaction_id
                )
            )
            if payment.transaction_id
            else None
        ),
        merchant_decision=payment.merchant_decision,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        attempts=[
            PaymentAttemptResponse(
                id=str(attempt.id),
                provider=attempt.provider,
                status=attempt.status,
                provider_reference=attempt.provider_reference,
                response_metadata=attempt.response_metadata,
                created_at=attempt.created_at,
            )
            for attempt in attempts
        ],
        timeline=_timeline(payment),
        metadata=payment.safe_metadata,
    )


def create_payment(
    session: Session,
    principal: Principal,
    request: PaymentCreate,
    *,
    idempotency_key: str | None,
    request_id: str,
    settings: Settings,
) -> PaymentResponse:
    key = _validate_key(idempotency_key)
    fingerprint = _fingerprint(request)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    existing = session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == principal.tenant_id,
            IdempotencyRecord.endpoint == PAYMENT_ENDPOINT,
            IdempotencyRecord.key_hash == key_hash,
        )
    )
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise AppError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency-Key was already used with a different request.",
                409,
            )
        return PaymentResponse.model_validate(existing.response_body)

    provider_status, payment_status, provider_reference, provider_metadata = mock_gateway_authorize(
        request
    )
    payment = PaymentIntent(
        tenant_id=principal.tenant_id,
        merchant_order_id=request.merchant_order_id,
        amount_minor=request.amount_minor,
        currency=request.currency.upper(),
        channel=request.channel.value,
        payment_method_label=request.payment_method.value,
        payment_status=payment_status,
        provider_status=provider_status,
        provider_reference=provider_reference,
        merchant_decision=f"merchant_policy_{payment_status}",
        safe_metadata=request.metadata,
    )
    session.add(payment)
    session.flush()
    session.add(
        PaymentAttempt(
            tenant_id=principal.tenant_id,
            payment_intent_id=payment.id,
            status=provider_status,
            provider_reference=provider_reference,
            response_metadata=provider_metadata,
        )
    )
    session.flush()

    transaction_request = CanonicalTransaction(
        transaction_id=f"pay_{payment.id.hex}",
        amount_minor=request.amount_minor,
        currency=request.currency,
        occurred_at=datetime.now(UTC),
        account_ref=request.account_ref,
        device_ref=request.device_ref,
        merchant_ref=request.merchant_ref,
        channel=request.channel,
        provider_status=provider_status,
        metadata={"source": "sandbox_checkout", "provider_event_type": "payment_attempt"},
    )
    payment.safe_metadata = transaction_request.metadata
    assessment_response = score_transaction(
        session,
        principal,
        transaction_request,
        request_id=request_id,
        idempotency_key=f"payment:{payment.id}",
        settings=settings,
    )
    assessment = session.scalar(
        select(Assessment)
        .where(
            Assessment.tenant_id == principal.tenant_id,
            Assessment.request_id == request_id,
        )
        .order_by(Assessment.created_at.desc())
    )
    transaction = session.scalar(
        select(Transaction).where(
            Transaction.tenant_id == principal.tenant_id,
            Transaction.external_transaction_id == transaction_request.transaction_id,
        )
    )
    payment.risk_score = assessment_response.risk_score
    payment.risk_level = str(assessment_response.risk_level)
    payment.risk_recommendation = "review" if assessment_response.risk_score >= 60 else "monitor"
    payment.assessment_id = assessment.id if assessment else None
    payment.transaction_id = transaction.id if transaction else None
    record_audit(
        session,
        tenant_id=principal.tenant_id,
        actor_type="api_key",
        actor_id=str(principal.api_key_id),
        action="sandbox_payment.completed",
        target_type="payment_intent",
        target_id=str(payment.id),
        request_id=request_id,
        details={
            "provider_status": provider_status,
            "payment_status": payment_status,
            "risk_recommendation": payment.risk_recommendation,
        },
    )
    response = _response(session, payment)
    session.add(
        IdempotencyRecord(
            tenant_id=principal.tenant_id,
            endpoint=PAYMENT_ENDPOINT,
            key_hash=key_hash,
            request_fingerprint=fingerprint,
            response_status=201,
            response_body=response.model_dump(mode="json"),
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.idempotency_ttl_seconds),
        )
    )
    # The scoring service commits first; this persists the payment updates.
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise AppError(
            "PAYMENT_CONFLICT", "The payment conflicts with existing data.", 409
        ) from exc
    return response


def get_payment(session: Session, tenant_id: UUID, payment_id: UUID) -> PaymentResponse:
    payment = session.scalar(
        select(PaymentIntent).where(
            PaymentIntent.id == payment_id, PaymentIntent.tenant_id == tenant_id
        )
    )
    if payment is None:
        raise AppError("PAYMENT_NOT_FOUND", "Payment was not found.", 404)
    return _response(session, payment)


def list_payments(session: Session, tenant_id: UUID, limit: int, offset: int) -> PaymentList:
    payments = list(
        session.scalars(
            select(PaymentIntent)
            .where(PaymentIntent.tenant_id == tenant_id)
            .order_by(PaymentIntent.created_at.desc(), PaymentIntent.id)
            .limit(limit)
            .offset(offset)
        ).all()
    )
    total = (
        session.scalar(
            select(func.count(PaymentIntent.id)).where(PaymentIntent.tenant_id == tenant_id)
        )
        or 0
    )
    return PaymentList(
        items=[_response(session, payment) for payment in payments],
        limit=limit,
        offset=offset,
        total=total,
    )
