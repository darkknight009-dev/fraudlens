"""Synchronous, bounded-timeout FraudLens API client."""

import uuid
from collections.abc import Mapping
from typing import Any

import httpx

from fraudlens_sdk.exceptions import (
    AuthenticationError,
    FraudLensError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from fraudlens_sdk.models import RiskAssessment, Transaction


class FraudLensClient:
    """Small integration client with no implicit retries."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 2.0,
        client: httpx.Client | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "FraudLensClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def score_transaction(
        self, transaction: Transaction, *, idempotency_key: str
    ) -> RiskAssessment:
        """Score one transaction; callers must explicitly provide idempotency."""

        if not idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        correlation_id = f"req_sdk_{uuid.uuid4().hex}"
        try:
            response = self._client.post(
                f"{self.base_url}/v1/transactions/score",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Idempotency-Key": idempotency_key,
                    "X-Correlation-ID": correlation_id,
                },
                json=transaction.model_dump(mode="json"),
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError("FraudLens request timed out.", request_id=correlation_id) from exc
        except httpx.HTTPError as exc:
            raise ServerError(
                "FraudLens transport request failed.", request_id=correlation_id
            ) from exc

        if response.status_code == 200:
            return RiskAssessment.model_validate(response.json())
        self._raise_for_response(response)
        raise AssertionError("unreachable")

    def _raise_for_response(self, response: httpx.Response) -> None:
        payload: Mapping[str, Any] = response.json() if response.content else {}
        error = payload.get("error", {}) if isinstance(payload, Mapping) else {}
        code = error.get("code") if isinstance(error, Mapping) else None
        message = (
            error.get("message") if isinstance(error, Mapping) else "FraudLens request failed."
        )
        request_id = error.get("request_id") if isinstance(error, Mapping) else None
        details = f" ({code})" if code else ""
        full_message = f"{message}{details}"
        if response.status_code in {401, 403}:
            raise AuthenticationError(full_message, code=code, request_id=request_id)
        if response.status_code in {400, 409, 422}:
            raise ValidationError(full_message, code=code, request_id=request_id)
        if response.status_code == 429:
            raise RateLimitError(full_message, code=code, request_id=request_id)
        if response.status_code >= 500:
            raise ServerError(full_message, code=code, request_id=request_id)
        raise FraudLensError(full_message, code=code, request_id=request_id)
