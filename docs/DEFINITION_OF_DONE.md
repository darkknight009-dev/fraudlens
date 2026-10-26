# Definition of Done

A feature is done only when all applicable items are satisfied.

## Product
- Acceptance criteria in the issue are met.
- Behavior matches the PRD and API contract.
- No unapproved scope expansion or payment-decision authority.

## Engineering
- Code is typed, readable, and modular.
- Validation and error handling are explicit.
- Database changes use Alembic migrations.
- Monetary arithmetic uses integer minor units or Decimal.
- Timestamps are timezone-aware UTC.
- Tenant scope is enforced at the data/service layer.
- Configuration and secrets are handled safely.

## Tests
- Unit tests cover core logic and boundary cases.
- Integration/contract tests cover changed APIs.
- Auth, scope, and cross-tenant cases are tested where relevant.
- Failure modes and idempotency are tested where relevant.
- Tests actually run; results are reported accurately.

## Security and privacy
- No secrets or sensitive data in source control or logs.
- No unnecessary payment credentials or card data.
- New endpoints have authentication/authorization decisions.
- Audit logging is included for security-sensitive actions.
- Threat model is updated when attack surface changes.

## Operations
- Health/readiness behavior remains correct.
- Metrics/logs are sufficient to diagnose failures.
- Timeout and retry behavior is bounded.
- Docs, `.env.example`, and deployment instructions are updated.

## Documentation
- README, API contract, configuration, and relevant ADRs are updated.
- Known limitations are stated.
- Demo data is labeled synthetic.
- No unverified performance or fraud-detection claims.
