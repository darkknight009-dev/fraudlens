"""Synchronous transaction scoring service."""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models.assessment import Assessment, RiskSignal
from app.models.idempotency import IdempotencyRecord
from app.models.transaction import Transaction
from app.schemas.scoring import (
    AssessmentStatus,
    DetectorStatus,
    RiskLevel,
    RiskSignalResponse,
    ScoreResponse,
    SignalSeverity,
    SignalSource,
)
from app.schemas.transactions import CanonicalTransaction
from app.services.alerts import create_alert_if_needed
from app.services.auth import Principal
from app.services.rules import aggregate_score, evaluate_rules, get_active_rules

SCORE_ENDPOINT = "/v1/transactions/score"


def _as_utc(value: datetime) -> datetime:
    """Normalize timezone-aware database values; SQLite may drop timezone metadata in tests."""

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _hash_value(value: str, tenant_id: UUID, pepper: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        f"{tenant_id}:{value}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _request_fingerprint(transaction: CanonicalTransaction) -> str:
    canonical = json.dumps(
        transaction.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _key_hash(idempotency_key: str) -> str:
    return hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()


def _validate_idempotency_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise AppError("IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key is required.", 400)
    normalized = value.strip()
    if len(normalized) > 255 or any(
        ord(character) < 33 or ord(character) > 126 for character in normalized
    ):
        raise AppError("INVALID_IDEMPOTENCY_KEY", "Idempotency-Key is invalid.", 400)
    return normalized


def score_transaction(
    session: Session,
    principal: Principal,
    transaction_input: CanonicalTransaction,
    request_id: str,
    idempotency_key: str | None,
    settings: Settings,
) -> ScoreResponse:
    key = _validate_idempotency_key(idempotency_key)
    fingerprint = _request_fingerprint(transaction_input)
    key_hash = _key_hash(key)
    now = datetime.now(UTC)
    existing_idempotency = session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == principal.tenant_id,
            IdempotencyRecord.endpoint == SCORE_ENDPOINT,
            IdempotencyRecord.key_hash == key_hash,
        )
    )
    if existing_idempotency is not None:
        if _as_utc(existing_idempotency.expires_at) <= now:
            session.delete(existing_idempotency)
            session.flush()
        elif existing_idempotency.request_fingerprint != fingerprint:
            raise AppError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency-Key was already used with a different request.",
                409,
            )
        else:
            return ScoreResponse.model_validate(existing_idempotency.response_body)

    existing_transaction = session.scalar(
        select(Transaction).where(
            Transaction.tenant_id == principal.tenant_id,
            Transaction.external_transaction_id == transaction_input.transaction_id,
        )
    )
    if existing_transaction is not None:
        raise AppError(
            "TRANSACTION_ALREADY_EXISTS",
            "The transaction reference already exists for this tenant.",
            409,
        )

    transaction = Transaction(
        tenant_id=principal.tenant_id,
        external_transaction_id=transaction_input.transaction_id,
        amount_minor=transaction_input.amount_minor,
        currency=transaction_input.currency,
        occurred_at=transaction_input.occurred_at,
        account_ref_hash=_hash_value(
            transaction_input.account_ref, principal.tenant_id, settings.api_key_hash_pepper
        ),
        device_ref_hash=(
            _hash_value(
                transaction_input.device_ref, principal.tenant_id, settings.api_key_hash_pepper
            )
            if transaction_input.device_ref
            else None
        ),
        merchant_ref=transaction_input.merchant_ref,
        channel=transaction_input.channel.value,
        provider_status=transaction_input.provider_status,
        safe_metadata=transaction_input.metadata,
    )
    session.add(transaction)
    session.flush()

    rule_set, configuration = get_active_rules(session, principal.tenant_id)
    rules, features = evaluate_rules(session, transaction, configuration)
    score, level = aggregate_score(rules, configuration)
    assessment = Assessment(
        tenant_id=principal.tenant_id,
        transaction_id=transaction.id,
        risk_score=score,
        risk_level=RiskLevel(level),
        mode=settings.risk_mode_default,
        assessment_status=AssessmentStatus.COMPLETE,
        rule_set_version=rule_set.version,
        model_version=None,
        feature_snapshot=features,
        detector_status={"rules": "complete", "ml": "disabled"},
        request_id=request_id,
    )
    session.add(assessment)
    session.flush()
    for signal in rules:
        session.add(
            RiskSignal(
                tenant_id=principal.tenant_id,
                assessment_id=assessment.id,
                reason_code=signal.reason_code,
                source=SignalSource.RULE,
                severity=SignalSeverity(signal.severity),
                message_template_key=signal.reason_code,
                evidence=signal.evidence,
                contribution=signal.contribution,
            )
        )

    response = ScoreResponse(
        assessment_id=f"assess_{assessment.id.hex}",
        transaction_id=transaction_input.transaction_id,
        risk_score=score,
        risk_level=RiskLevel(level),
        mode=settings.risk_mode_default,
        assessment_status=AssessmentStatus.COMPLETE,
        signals=[
            RiskSignalResponse(
                reason_code=signal.reason_code,
                message=signal.message,
                source=SignalSource.RULE,
                severity=SignalSeverity(signal.severity),
                evidence=signal.evidence,
                contribution=signal.contribution,
            )
            for signal in rules
        ],
        detector_status=DetectorStatus(rules="complete", ml="disabled"),
        rule_set_version=rule_set.version,
        model_version=None,
        request_id=request_id,
    )
    session.add(
        IdempotencyRecord(
            tenant_id=principal.tenant_id,
            endpoint=SCORE_ENDPOINT,
            key_hash=key_hash,
            request_fingerprint=fingerprint,
            response_status=200,
            response_body=response.model_dump(mode="json"),
            expires_at=now + timedelta(seconds=settings.idempotency_ttl_seconds),
        )
    )
    create_alert_if_needed(session, assessment, request_id=request_id)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise AppError(
            "SCORING_CONFLICT", "The scoring request conflicts with existing data.", 409
        ) from exc
    return response
