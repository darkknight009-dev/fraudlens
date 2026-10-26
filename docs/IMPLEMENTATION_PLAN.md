# Implementation Plan

Implement as vertical slices. Each milestone must pass its acceptance criteria before the next begins.

## Milestone 0 — Repository and engineering foundation
- Initialize backend/frontend directories and package managers.
- Add formatting, linting, type checks, tests, `.gitignore`, `.env.example`, Docker Compose.
- Add CI workflow.
- Add docs links and license decision placeholder.
**Acceptance:** clean install instructions work; secrets and generated data are ignored; basic checks run in CI.

## Milestone 1 — API skeleton and persistence
- FastAPI app, settings, structured logging, error envelope, correlation ID.
- PostgreSQL connection and SQLAlchemy setup.
- Alembic migrations.
- Liveness/readiness endpoints.
- Tenant/API-key models and development-only bootstrap command.
- Authentication dependency and scopes.
**Acceptance:** migration from empty DB works; health checks work; unauthenticated protected request returns 401; scopes are enforced; tenant isolation tests exist.

## Milestone 2 — Canonical transaction and deterministic rules
- Pydantic canonical transaction schema.
- Input normalization and validation.
- Transaction persistence and unique/idempotent behavior.
- Versioned rule config and rule evaluation.
- Risk aggregator with reason codes.
- `POST /v1/transactions/score`.
**Acceptance:** valid transaction produces reproducible assessment; invalid inputs are rejected; same idempotency key returns same result; conflicting body returns 409; score stays 0–100; no payment outcome is changed.

## Milestone 3 — Python SDK and sample merchant
- Typed SDK client and exceptions.
- Timeout and idempotency support.
- Example merchant simulator.
- Shadow mode clearly implemented and demonstrated.
**Acceptance:** simulator can send transactions through SDK; simulator's original outcome remains unchanged; SDK contract tests pass.

## Milestone 4 — Alerts and investigations
- Assessment/signal persistence.
- Alert/case deduplication.
- Alert list/detail, status transitions, notes, dispositions.
- Audit events.
**Acceptance:** alert lifecycle works; unauthorized and cross-tenant access fail; all state transitions create audit events.

## Milestone 5 — Synthetic data and ML baseline
- Synthetic dataset generator with documented scenarios and seeds.
- Feature pipeline with point-in-time correctness.
- Baseline Isolation Forest or similar detector behind interface.
- Evaluation script and report.
- Versioned model artifact metadata.
**Acceptance:** no scenario labels leak into features; reproducible train/test split; metrics and limitations documented; API indicates model status/version.

## Milestone 6 — Frontend dashboard
- React + TypeScript + Tailwind.
- API client, tenant/session handling suitable for demo.
- Transaction/assessment table, alert filters, case detail, risk signal view, basic charts.
- Clear synthetic/demo and shadow-mode banners.
**Acceptance:** analyst journey works end-to-end; errors/loading/empty states handled; build and tests pass; no integration key shipped to browser.

## Milestone 7 — Hardening and operations
- Rate limiting, request-size limits, security headers, dependency scanning.
- Retention/deletion job and tests.
- Load test and latency report.
- Backup/restore instructions and exercise.
- OpenTelemetry instrumentation or compatible metrics.
**Acceptance:** threat model reviewed; tenant isolation and redaction tests pass; failure behavior documented; release checklist complete for local demo.

## Milestone 8 — Asynchronous events and webhooks
- Durable queue abstraction; use Redis only if justified for MVP.
- Event ingestion endpoint or broker adapter.
- Signed webhooks, retry/backoff, delivery logs, replay.
- Duplicate/replay protection.
**Acceptance:** event processing is idempotent; webhook signatures verified; delivery failures don't block scoring; replay is audited.

## Milestone 9 — Customer-hosted deployment profile
- Hardened container image and non-root runtime.
- External secrets support.
- Upgrade/rollback, backup responsibility, network requirements.
- Configuration validation and release versioning.
**Acceptance:** clean customer-like environment can deploy from docs; no developer-only shortcuts remain.

## Work sequencing rules
- Do not start ML before deterministic scoring and evaluation harness are stable.
- Do not start dashboard polish before API + SDK + simulator work.
- Do not add payment blocking.
- Do not add cloud vendor dependencies without a reason and approval.
- Update `CHANGELOG.md` and relevant docs with each milestone.
