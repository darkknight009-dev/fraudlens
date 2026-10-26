"""Run a synthetic merchant flow without changing the merchant outcome."""

import os
from datetime import UTC, datetime
from uuid import uuid4

from fraudlens_sdk import FraudLensClient, RiskAssessment, Transaction
from fraudlens_sdk.exceptions import FraudLensError


def original_merchant_outcome(transaction: Transaction) -> str:
    """The merchant's existing policy remains the sole payment decision-maker."""

    return "approved" if transaction.amount_minor < 10_000_000 else "review"


def build_transaction(index: int) -> Transaction:
    return Transaction(
        transaction_id=f"sim_txn_{index:04d}",
        amount_minor=2_500 + index * 100,
        currency="INR",
        occurred_at=datetime.now(UTC),
        account_ref="sim_account_001",
        device_ref="sim_device_001",
        merchant_ref="sim_merchant_001",
        channel="upi",
        provider_status="pending",
        metadata={"source": "merchant_simulator", "integration_version": "0.1"},
    )


def main() -> None:
    base_url = os.environ.get("FRAUDLENS_BASE_URL", "http://localhost:8000")
    api_key = os.environ.get("FRAUDLENS_API_KEY")
    if not api_key:
        raise SystemExit("Set FRAUDLENS_API_KEY to the development key printed by bootstrap.")

    transaction = build_transaction(1)
    original_outcome = original_merchant_outcome(transaction)
    try:
        with FraudLensClient(base_url, api_key, timeout=2.0) as client:
            assessment: RiskAssessment = client.score_transaction(
                transaction,
                idempotency_key=f"sim-{uuid4().hex}",
            )
    except FraudLensError as exc:
        print(f"FraudLens advisory unavailable: {exc}")
        print(f"Merchant outcome unchanged: {original_outcome}")
        return

    print("DEMO / SYNTHETIC DATA")
    print(f"SHADOW MODE: {assessment.mode}")
    print(f"Assessment: {assessment.risk_level} ({assessment.risk_score}/100)")
    print(f"Merchant outcome unchanged: {original_outcome}")


if __name__ == "__main__":
    main()
