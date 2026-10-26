"""Optional reviewed model artifact loading and point-in-time inference."""

from datetime import UTC, timedelta
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.transaction import Transaction
from app.services.detectors.isolation_forest import IsolationForestDetector


def channel_code(channel: str) -> int:
    return {"card": 0, "bank_transfer": 1, "wallet": 2, "upi": 3}.get(channel, 4)


def transaction_features(session: Session, transaction: Transaction) -> list[float]:
    """Build only values available when this transaction was observed."""

    window_start = transaction.occurred_at - timedelta(minutes=5)
    account_velocity = (
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
    device_velocity = 0
    if transaction.device_ref_hash:
        device_velocity = (
            session.scalar(
                select(func.count(Transaction.id)).where(
                    Transaction.tenant_id == transaction.tenant_id,
                    Transaction.device_ref_hash == transaction.device_ref_hash,
                    Transaction.occurred_at >= window_start,
                    Transaction.occurred_at <= transaction.occurred_at,
                )
            )
            or 0
        )
    occurred_at = transaction.occurred_at
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    return [
        float(transaction.amount_minor),
        float(occurred_at.hour),
        float(account_velocity),
        float(device_velocity),
        float(channel_code(transaction.channel)),
    ]


def load_detector(settings: Settings) -> tuple[IsolationForestDetector | None, str | None]:
    if not settings.model_artifact_path:
        return None, None
    path = Path(settings.model_artifact_path)
    if not path.is_file():
        raise FileNotFoundError(f"configured model artifact does not exist: {path}")
    detector: Any = joblib.load(path)
    if not isinstance(detector, IsolationForestDetector):
        raise TypeError("configured model artifact is not an IsolationForestDetector")
    return detector, detector.version
