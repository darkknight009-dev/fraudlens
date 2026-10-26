# Integration Design

## 1. Integration modes
### A. Synchronous REST scoring
Use when the integrating system needs a risk assessment during its existing workflow. The customer owns the timeout and decision policy. FraudLens only returns an assessment.

### B. Asynchronous event ingestion
Use when continuous monitoring is desired without adding scoring latency to payment authorization. Events are accepted, acknowledged, processed, and surfaced through alerts/webhooks. This mode requires durable queueing and retry semantics; it is a later milestone.

### C. Customer-hosted deployment
Run containerized FraudLens within the customer's cloud/private environment. This is a later deployment profile and requires operational documentation, security review, and compatibility testing.

## 2. Canonical transaction schema
Required:
- `transaction_id`: customer/provider transaction reference; scoped to tenant.
- `amount_minor`: integer amount in minor currency units; non-negative.
- `currency`: ISO 4217 code.
- `occurred_at`: timezone-aware ISO 8601 timestamp.
- `account_ref`: pseudonymous customer/account reference.
- `channel`: enum/string such as `card`, `bank_transfer`, `wallet`, `upi`, `other`.
Optional:
- `merchant_ref`, `device_ref`, `ip_risk_features` (only minimized/coarsened fields), `country_code`, `payment_method_family`, `provider_status`, `metadata` (strict allowlist).
Never accept or store PAN, CVV, PIN, OTP, passwords, bank login credentials, or authentication secrets.

Use `amount_minor` rather than `amount` to avoid currency precision ambiguity. For INR, ₹25,000.00 is `2500000` paise.

## 3. Field mapping
- Mapping is explicit per integration.
- Required canonical fields must map to a source field or a documented safe default if allowed.
- Unknown fields are dropped by default and never become features automatically.
- Mapping changes are versioned and audited.
- Validate mapping before activating it using representative synthetic sample payloads.
- Reject ambiguous currency/amount conversion rather than guessing.

## 4. API keys
- Keys are generated server-side, shown once, and stored as a secure hash.
- Include key ID/prefix for lookup; never store plaintext key.
- Scopes: `transactions:score`, `transactions:read`, `cases:read`, `cases:write`, `config:read`, `config:write`, `audit:read`.
- Support revocation, expiry, rotation overlap, and audit events.
- Dashboard user authentication should eventually use OIDC/OAuth; do not reuse long-lived integration API keys in browsers.

## 5. Idempotency
- Scoring POST accepts `Idempotency-Key`.
- Scope idempotency by tenant and endpoint.
- Same key + same request fingerprint returns original assessment.
- Same key + different request body returns `409 IDEMPOTENCY_KEY_REUSED`.
- Retain idempotency records for a documented, configurable window (initial default: 24 hours for MVP).
- Duplicate event ingestion must not create duplicate cases or webhook events.

## 6. Latency and timeout guidance
- Client must configure a strict timeout appropriate to its authorization SLA.
- FraudLens should not require third-party LLM calls for the synchronous scoring path.
- The API should return a complete response or a typed error/degraded state within its configured budget.
- Do not automatically retry non-idempotent requests without an idempotency key.
- Record p50/p95/p99 latency by endpoint and tenant without logging sensitive payloads.

## 7. Shadow mode
- Default mode is `shadow`.
- `shadow` computes and stores assessments but cannot alter payment outcomes.
- `advisory` returns results for customer policy evaluation but still does not act on payments itself.
- No `block` or `decline` action is implemented in MVP.
- Responses must include `mode`.
- Dashboard must visibly label demo/synthetic data and shadow mode.

## 8. SDK
Initial Python SDK requirements:
- typed `Transaction` and `RiskAssessment` models
- configurable base URL and API key
- timeout configuration
- automatic correlation ID
- explicit idempotency key support
- typed exceptions for auth, validation, rate limiting, timeout, and server failures
- no implicit infinite retries
- redacted logging
- package version and compatibility policy
- example using environment variables, not embedded credentials

## 9. Webhooks (later milestone)
- Sign payload using HMAC-SHA256 and timestamp; reject stale/replayed signatures.
- Include event ID, event type, created timestamp, tenant ID, and minimal payload.
- Retries use bounded exponential backoff and jitter.
- Expose delivery attempt history and manual replay with audit.
- Consumers must be idempotent.
- Never put secrets or full sensitive payloads in webhook body.
