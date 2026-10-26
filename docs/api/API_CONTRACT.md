# API Contract — `/v1`

This is the initial proposed contract. Implement only endpoints scheduled in the current milestone; keep this document aligned with generated OpenAPI.

## Conventions
- Base path: `/v1`
- Content type: `application/json`
- Authentication: `Authorization: Bearer <integration_api_key>`
- UTC ISO 8601 timestamps.
- Money: `amount_minor` integer + ISO currency code.
- Every response includes or propagates `request_id`/correlation ID.
- Error format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [],
    "request_id": "req_..."
  }
}
```
Never expose stack traces, SQL, secret values, or internal infrastructure details in API errors.

## Endpoints
### `GET /health/live`
Liveness only; does not require database availability. Returns `{"status":"alive"}`.

### `GET /health/ready`
Checks required dependencies and configuration. Returns 200 when ready, otherwise 503 with a safe dependency status summary.

### `POST /v1/transactions/score`
Synchronous risk scoring. Requires `transactions:score`.

Headers:
- `Idempotency-Key`: required for the scoring endpoint. The server returns `400 IDEMPOTENCY_KEY_REQUIRED` when it is absent.
- `X-Correlation-ID`: optional client-generated ID, validated and length-limited.

Request:
```json
{
  "transaction_id": "txn_10001",
  "amount_minor": 2500000,
  "currency": "INR",
  "occurred_at": "2026-10-26T15:30:00Z",
  "account_ref": "acct_pseudo_501",
  "device_ref": "device_pseudo_91",
  "merchant_ref": "merchant_demo_1",
  "channel": "upi",
  "provider_status": "pending",
  "metadata": {
    "source": "merchant_simulator"
  }
}
```
`metadata` must be size-limited and allowlisted. No raw credentials or payment-card data.

Response:
```json
{
  "assessment_id": "assess_...",
  "transaction_id": "txn_10001",
  "risk_score": 67,
  "risk_level": "medium",
  "mode": "shadow",
  "assessment_status": "complete",
  "signals": [
    {
      "reason_code": "HIGH_TRANSACTION_VELOCITY",
      "message": "Transaction frequency exceeded the configured threshold.",
      "source": "rule",
      "severity": "high",
      "evidence": {
        "window_minutes": 5,
        "observed_count": 12,
        "configured_threshold": 10
      }
    }
  ],
  "detector_status": {
    "rules": "complete",
    "ml": "disabled"
  },
  "rule_set_version": "rules-v1",
  "model_version": null,
  "request_id": "req_..."
}
```
Values above are illustrative only. The system must compute them from the request, available tenant history, and active configuration.

Potential status codes:
- `200`: assessment returned, including documented partial/degraded result.
- `400`: malformed request or missing/invalid idempotency key.
- `401`: missing/invalid credential.
- `403`: valid credential lacks scope.
- `409`: conflicting transaction or idempotency state, including `IDEMPOTENCY_KEY_REUSED`.
- `422`: semantic validation failure.
- `429`: rate limit exceeded.
- `503`: service cannot provide a safe assessment according to configured behavior.
- `500`: unexpected internal error with no sensitive details.

### `GET /v1/transactions/{transaction_id}/assessments`
List assessments for a transaction, tenant-scoped and paginated. Requires `transactions:read`.

### `GET /v1/alerts`
List alerts with filters: risk level, status, date range, reason code. Requires `cases:read`.

### `GET /v1/alerts/{alert_id}`
Return alert details and linked assessment. Requires `cases:read`.

### `PATCH /v1/alerts/{alert_id}`
Update allowed fields such as status, assignee, and disposition. Requires `cases:write`. Every state transition is validated and audited.

### `POST /v1/alerts/{alert_id}/notes`
Add a bounded-length analyst note. Requires `cases:write`. Do not include secrets or unnecessary personal information.

### `GET /v1/config/rules`
Read active tenant rule configuration. Requires `config:read`.

### `PUT /v1/config/rules`
Validate and replace rule configuration as a new version. Requires `config:write`. Changes must be audited and support rollback.

The active configuration uses the strict rule schema implemented by the service. Historical versions are not overwritten; a replacement deactivates the previous active version and creates a new version.

### `GET /v1/audit-events`
Paginated audit events for authorized administrators. Requires `audit:read`.

### Webhook management (Milestone 8)

- `POST /v1/webhook-endpoints` registers an HTTPS endpoint and returns its secret once. Requires `config:write`.
- `GET /v1/webhook-endpoints` lists endpoint metadata without secrets. Requires `config:read`.
- `GET /v1/webhook-deliveries` lists delivery status and bounded attempt metadata. Requires `config:read`.
- `POST /v1/webhook-deliveries/{delivery_id}/replay` requeues a failed delivery. Requires `config:write`.

Scoring and alert creation only enqueue durable delivery records. Network delivery runs asynchronously and cannot change the synchronous scoring response.

### `POST /v1/events` (Milestone 8)

Accepts `{ "event_id": "...", "transaction": <canonical transaction> }`, requires `transactions:score`, persists the event, and returns `202 Accepted`. Duplicate tenant-scoped event IDs return the existing status and never create a second inbox record. `make event-process` processes a bounded batch using the same scoring service.

## Pagination
Use cursor pagination where feasible, or `limit` + `offset` for MVP. Enforce a maximum page size (e.g. 100). Sort order must be deterministic.

## Idempotency behavior
- Same tenant + endpoint + key + same canonical request fingerprint: return the original response.
- Same key with different fingerprint: `409 IDEMPOTENCY_KEY_REUSED`.
- Retention window: configurable; initial default 24 hours.
- Prevent duplicate case creation when the same transaction event is processed repeatedly.

## Compatibility
- Do not make breaking changes within `/v1` without a documented migration plan.
- Add optional response fields when backward-compatible.
- Validate requests strictly; document deprecations and minimum SDK versions.
- Generate and test OpenAPI schema as part of CI.
