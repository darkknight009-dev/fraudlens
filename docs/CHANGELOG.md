# Changelog

All notable project changes should be recorded here.

## Unreleased
- Initial product, architecture, API, security, testing, operations, and implementation specifications.
- Milestone 0 completed: Python/FastAPI and React/TypeScript project setup, environment hygiene, Compose configuration, CI checks, and local development documentation.
- Milestone 1 implementation added: validated settings, structured errors and correlation IDs, health/readiness routes, SQLAlchemy models, Alembic foundation migration, API-key authentication/scopes, tenant-scoped repository access, development bootstrap, and PostgreSQL CI migration verification.
- Milestone 2 implementation added: canonical transaction validation, tenant-scoped transaction and assessment persistence, versioned deterministic rules, explainable bounded risk aggregation, idempotency records, and `POST /v1/transactions/score` in default shadow mode.
- Milestone 3 implementation added: typed Python SDK, bounded timeout/error handling, explicit idempotency and correlation support, SDK contract tests, and synthetic shadow-mode merchant simulator.
- Milestone 4 implementation added: tenant-scoped alert/case lifecycle, deduplicated high-risk alert creation, notes, dispositions, assessment history, audit recording, and paginated alert/audit APIs.
- Milestone 5 implementation added: deterministic synthetic dataset generator, point-in-time feature extraction, pluggable Isolation Forest detector, reproducible evaluation script, and ML limitations report.
- Milestone 6 implementation added: browser-safe React/TypeScript analyst dashboard with synthetic/shadow banners, alert filtering, case detail, explainable signals, status updates, and notes.
- Milestone 7 implementation added: request limits, process-local rate limiting, security headers, metrics endpoint, retention deletion tooling/tests, latency probe, and backup/restore runbook.
- Milestone 8 implementation added: encrypted webhook endpoint secrets, durable delivery records, HMAC signatures, bounded retries/dead letters, replay controls, SSRF-safe URL validation, and asynchronous dispatch CLI.
- Milestone 9 implementation added: non-root container runtime, customer-hosted deployment profile, configuration validation command, and release/rollback operational documentation.
- Rule configuration API completed: strict tenant-scoped read/replace endpoints with immutable versions and audit records.
- Durable event inbox completed: asynchronous canonical transaction ingestion, duplicate event protection, and bounded processing CLI.
- Frontend replaced with a Next.js 16 live-data operations console: server-only API proxy, no seeded demo records, empty-state handling, dense queue triage, case controls, and analyst notes.
- Operations console completed: working Overview, Alert queue, Transactions, Rules, Audit trail, and Webhooks sections mapped to their backend scopes and actions.
