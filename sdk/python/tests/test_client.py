import httpx
import pytest
from fraudlens_sdk import FraudLensClient, Transaction
from fraudlens_sdk.exceptions import (
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


def transaction() -> Transaction:
    return Transaction(
        transaction_id="txn_sdk_1",
        amount_minor=100,
        currency="INR",
        occurred_at="2026-10-26T15:30:00Z",
        account_ref="acct_sdk_1",
        channel="upi",
    )


def client_for(handler) -> FraudLensClient:
    return FraudLensClient(
        "http://fraudlens.test",
        "fl_test_key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_score_transaction_returns_typed_assessment() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Idempotency-Key"] == "sdk-key-1"
        assert request.headers["X-Correlation-ID"].startswith("req_sdk_")
        return httpx.Response(
            200,
            json={
                "assessment_id": "assess_1",
                "transaction_id": "txn_sdk_1",
                "risk_score": 0,
                "risk_level": "low",
                "mode": "shadow",
                "assessment_status": "complete",
                "signals": [],
                "detector_status": {"rules": "complete", "ml": "disabled"},
                "rule_set_version": "rules-v1",
                "model_version": None,
                "request_id": "req_sdk_1",
            },
        )

    with client_for(handler) as client:
        result = client.score_transaction(transaction(), idempotency_key="sdk-key-1")
    assert result.risk_score == 0
    assert result.mode == "shadow"


@pytest.mark.parametrize(
    ("status", "exception"),
    [(401, AuthenticationError), (422, ValidationError), (429, RateLimitError)],
)
def test_http_errors_are_typed(status: int, exception: type[Exception]) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status, json={"error": {"code": "TEST", "message": "failed", "request_id": "req_1"}}
        )

    with client_for(handler) as client:
        with pytest.raises(exception):
            client.score_transaction(transaction(), idempotency_key="sdk-key-1")


def test_timeout_is_typed() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    with client_for(handler) as client:
        with pytest.raises(TimeoutError):
            client.score_transaction(transaction(), idempotency_key="sdk-key-1")
