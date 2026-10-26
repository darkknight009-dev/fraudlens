"""Configurable deletion of expired local data."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.alert import Alert, CaseNote
from app.models.assessment import Assessment, RiskSignal
from app.models.audit_event import AuditEvent
from app.models.idempotency import IdempotencyRecord
from app.models.transaction import Transaction


def run_retention(session: Session, settings: Settings) -> dict[str, int]:
    """Delete records past configured defaults; never logs or returns payload data."""

    now = datetime.now(UTC)
    cutoffs = {
        "transactions": now - timedelta(days=settings.retention_transaction_days),
        "audit_events": now - timedelta(days=settings.retention_audit_days),
        "idempotency_records": now - timedelta(seconds=settings.idempotency_ttl_seconds),
    }
    deleted: dict[str, int] = {}
    expired_models: list[tuple[str, Any, datetime]] = [
        ("case_notes", CaseNote, cutoffs["transactions"]),
        ("alerts", Alert, cutoffs["transactions"]),
        ("risk_signals", RiskSignal, cutoffs["transactions"]),
        ("assessments", Assessment, cutoffs["transactions"]),
        ("transactions", Transaction, cutoffs["transactions"]),
        ("audit_events", AuditEvent, cutoffs["audit_events"]),
        ("idempotency_records", IdempotencyRecord, cutoffs["idempotency_records"]),
    ]
    for name, model, cutoff in expired_models:
        result = session.execute(delete(model).where(model.created_at < cutoff))
        deleted[name] = result.rowcount or 0
    session.commit()
    return deleted
