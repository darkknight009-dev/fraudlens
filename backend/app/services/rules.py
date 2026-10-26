"""Deterministic, versioned rule evaluation."""

from datetime import timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.rule_set import RuleSetVersion
from app.models.transaction import Transaction

DEFAULT_RULE_CONFIGURATION: dict[str, Any] = {
    "version": "rules-v1",
    "amount": {"threshold_minor": 1_000_000, "contribution": 35},
    "velocity": {"window_minutes": 5, "threshold": 10, "contribution": 45},
    "provider_status": {"statuses": ["failed", "declined"], "contribution": 25},
    "levels": {"medium": 30, "high": 60, "critical": 85},
}


class AmountRule(BaseModel):
    threshold_minor: int = Field(ge=0)
    contribution: int = Field(ge=0, le=100)


class VelocityRule(BaseModel):
    window_minutes: int = Field(gt=0, le=1_440)
    threshold: int = Field(gt=0, le=100_000)
    contribution: int = Field(ge=0, le=100)


class ProviderStatusRule(BaseModel):
    statuses: list[str] = Field(min_length=1, max_length=20)
    contribution: int = Field(ge=0, le=100)


class RiskLevelThresholds(BaseModel):
    medium: int = Field(ge=0, le=100)
    high: int = Field(ge=0, le=100)
    critical: int = Field(ge=0, le=100)


class RuleConfiguration(BaseModel):
    version: str = Field(min_length=1, max_length=64)
    amount: AmountRule
    velocity: VelocityRule
    provider_status: ProviderStatusRule
    levels: RiskLevelThresholds


class RuleSignal:
    def __init__(
        self,
        reason_code: str,
        message: str,
        severity: str,
        evidence: dict[str, Any],
        contribution: int,
    ) -> None:
        self.reason_code = reason_code
        self.message = message
        self.severity = severity
        self.evidence = evidence
        self.contribution = contribution


def get_active_rules(session: Session, tenant_id: UUID) -> tuple[RuleSetVersion, RuleConfiguration]:
    rule_set = session.scalar(
        select(RuleSetVersion)
        .where(RuleSetVersion.tenant_id == tenant_id, RuleSetVersion.is_active.is_(True))
        .order_by(RuleSetVersion.created_at.desc())
    )
    if rule_set is None:
        rule_set = RuleSetVersion(
            tenant_id=tenant_id,
            version=DEFAULT_RULE_CONFIGURATION["version"],
            configuration=DEFAULT_RULE_CONFIGURATION,
            created_by="system-default",
            is_active=True,
        )
        session.add(rule_set)
        session.flush()
    try:
        configuration = RuleConfiguration.model_validate(rule_set.configuration)
    except ValueError as exc:
        raise AppError(
            "INVALID_RULE_CONFIGURATION",
            "The active tenant rule configuration is invalid.",
            503,
        ) from exc
    return rule_set, configuration


def evaluate_rules(
    session: Session,
    transaction: Transaction,
    configuration: RuleConfiguration,
) -> tuple[list[RuleSignal], dict[str, object]]:
    signals: list[RuleSignal] = []
    window_start = transaction.occurred_at - timedelta(
        minutes=configuration.velocity.window_minutes
    )
    velocity_count = (
        session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.tenant_id == transaction.tenant_id,
                Transaction.account_ref_hash == transaction.account_ref_hash,
                Transaction.occurred_at >= window_start,
                Transaction.occurred_at <= transaction.occurred_at,
            )
        )
        or 0
    )

    if transaction.amount_minor >= configuration.amount.threshold_minor:
        signals.append(
            RuleSignal(
                "HIGH_TRANSACTION_AMOUNT",
                "Transaction amount exceeded the configured threshold.",
                "high",
                {
                    "amount_minor": transaction.amount_minor,
                    "configured_threshold_minor": configuration.amount.threshold_minor,
                },
                configuration.amount.contribution,
            )
        )
    if velocity_count > configuration.velocity.threshold:
        signals.append(
            RuleSignal(
                "HIGH_TRANSACTION_VELOCITY",
                "Transaction frequency exceeded the configured threshold.",
                "high",
                {
                    "window_minutes": configuration.velocity.window_minutes,
                    "observed_count": velocity_count,
                    "configured_threshold": configuration.velocity.threshold,
                },
                configuration.velocity.contribution,
            )
        )
    if transaction.provider_status and transaction.provider_status.lower() in {
        status.lower() for status in configuration.provider_status.statuses
    }:
        signals.append(
            RuleSignal(
                "PROVIDER_STATUS_RISK",
                "Provider status matched a configured risk condition.",
                "medium",
                {"provider_status": transaction.provider_status},
                configuration.provider_status.contribution,
            )
        )

    features: dict[str, object] = {
        "amount_minor": transaction.amount_minor,
        "velocity_count": velocity_count,
        "velocity_window_minutes": configuration.velocity.window_minutes,
        "provider_status_present": transaction.provider_status is not None,
    }
    return signals, features


def aggregate_score(signals: list[RuleSignal], configuration: RuleConfiguration) -> tuple[int, str]:
    score = min(100, sum(signal.contribution for signal in signals))
    if score >= configuration.levels.critical:
        return score, "critical"
    if score >= configuration.levels.high:
        return score, "high"
    if score >= configuration.levels.medium:
        return score, "medium"
    return score, "low"
