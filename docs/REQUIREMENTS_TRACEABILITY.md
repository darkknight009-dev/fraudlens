# FraudLens Requirements-to-Implementation Traceability

**Baseline date:** 2026-10-26  
**Implementation status:** Milestones 0–9 implemented; the Next.js live-data console is implemented; live PostgreSQL verification depends on the local Docker runtime.

## Current repository state

The repository contains the backend, typed SDK, merchant simulator, Next.js operations console, migrations, and generated API checks. The console has no seeded demo records and displays an empty state when the tenant has no live alerts.

## Traceability checklist

Status values: `Not started`, `Planned M0`, `Planned M1`, `Later`, and `Needs decision`.

| Requirement / source | Acceptance evidence | Implementation target | Status |
|---|---|---|---|
| PRD FR-01; Security §3; ADR-0002 | Authenticated caller resolves tenant; missing, invalid, expired, and revoked keys fail safely; scopes are enforced | API-key model, auth dependency, tenant context, scope dependency, security tests | M1 implemented; PostgreSQL runtime pending |
| PRD FR-02; Integration §2; ADR-0003 | Canonical fields and validation are documented and represented by typed schemas | Versioned Pydantic transaction schema and validation tests | M2 implemented |
| PRD FR-03; Integration §3 | Explicit mappings validate before activation; unknown fields are dropped | Adapter/mapping module and configuration validation | Later / M2+ |
| PRD FR-04; API §32–89 | Versioned scoring response includes score, level, mode, status, signals, versions, detector status, and request ID | `/v1/transactions/score` and contract tests | M2 implemented |
| PRD FR-05; Architecture §18–21 | Tenant-scoped, versioned deterministic rules produce traceable signals | Rule configuration, evaluator, and aggregation service | M2 implemented |
| PRD FR-06; ML Governance; ADR-0004 | Detector is behind an interface; evaluation prevents leakage and does not call anomaly score a probability | Detector interface and evaluation pipeline | M5 implemented; API activation remains governed |
| PRD FR-07; Integration §7; ADR-0002 | Shadow is the default and no FraudLens code path changes payment outcomes | Mode configuration, response field, simulator proof | Later / M2–M3 |
| PRD FR-08; Data Model §65–82 | Alert/case lifecycle, deduplication, notes, dispositions, and tenant isolation work | Alert/case service and API | M4 implemented |
| PRD FR-09; Integration §9 | Signed, retried, replayable webhooks do not block scoring | Webhook dispatcher, encrypted endpoint secrets, delivery store, replay API | M8 implemented |
| PRD FR-10; Data Model §94–103; Security §6 | Security-sensitive actions create append-oriented redacted audit events | Audit service and audit API | M4 implemented; coverage expands later |
| PRD FR-11; API §25–30; Runbook §3–5 | Liveness, readiness, correlation IDs, structured logs, and operational signals are available | Health routes, middleware, logging, metrics, security headers | M7 implemented |
| PRD FR-12; Security §2 | Retention defaults are documented and deletion is tested before real pilot use | Retention configuration/job and tests | Later / M7 |
| PRD FR-13 | Analyst dashboard supports transaction, alert, case, and score workflows | Next.js live-data operations console with server-side API proxy | M6 revised and implemented; OIDC remains enterprise follow-up |
| PRD FR-14; Integration §8 | Typed SDK and simulator demonstrate auth, timeout, idempotency, and shadow behavior | Python SDK and merchant simulator | M3 implemented |
| NFR security; Security §2–3 | No payment credentials; secrets are hashed/rotated; input and tenant boundaries are protected | Secret-safe config, validation, auth, isolation tests | M1 foundation implemented; hardening later |
| NFR reliability; Architecture §111–118 | Bounded dependencies, explicit readiness/failure states, and no hidden payment decision | Health/readiness and failure policy | M1 implemented; scoring later |
| NFR performance; PRD §110, §124 | Synthetic load reports p50/p95/p99 latency and error rate | Load test and report | M7 tooling implemented; live report requires running service |
| NFR maintainability/portability; M0 | Fresh setup, pinned dependencies, Docker Compose, migrations, checks, and CI are reproducible | Project tooling and local runtime | M0 complete; Docker runtime pending host availability |
| API §1–23 | `/v1` conventions, UTC timestamps, safe error envelope, and request ID are consistent | Settings, middleware, exception handlers, API tests | M1 implemented; scoring contract later |
| API §26–30 | Live endpoint does not require DB; ready endpoint checks required dependencies and returns safe 503 | `/health/live`, `/health/ready` | M1 implemented; PostgreSQL runtime pending |
| API §32–99 | Scoring auth, validation, idempotency, status codes, and degraded behavior match contract | Scoring route/service and contract tests | M2 implemented; degraded model path later |
| API §102–124 | Tenant-scoped pagination, case/config/audit permissions, and transitions are enforced | Assessment, alert, case, note, and audit routes | M4 implemented; config routes later |
| Data Model §1–126; ADR-0005 | PostgreSQL tables, constraints, UTC timestamps, indexes, and tenant-scoped queries migrate from empty DB | Initial metadata plus tenant/API-key/scoring migrations; remaining entities by milestone | Implemented; empty-DB runtime pending CI/Docker |
| Testing Strategy §1–80 | Unit, integration, contract, security, and CI checks run and report actual results | Test layout and CI gates | M0 foundation complete; expanded later |
| Implementation Plan M0 | Clean install instructions, ignored secrets/generated data, and basic CI checks work | Project skeleton and developer tooling | M0 complete; Compose runtime pending host availability |
| Implementation Plan M1 | Empty-DB migration works; health checks work; protected requests return 401; scopes and isolation are tested | FastAPI foundation, DB, auth, tenant context | Implemented; PostgreSQL runtime pending |
| Implementation Plan M2 | Valid transaction produces reproducible assessment; invalid inputs reject; idempotency returns original result; conflicts return 409; score is bounded; payment outcome is untouched | Canonical schemas, transaction/scoring models, deterministic rules, scoring endpoint, tests | M2 implemented |
| Implementation Plan M3 | Simulator sends through SDK; original merchant outcome remains unchanged; SDK handles contract failures safely | Typed SDK, exceptions, timeout behavior, simulator, SDK tests | M3 implemented |
| ADR-0001 | Modular monolith with clear module boundaries; no premature services | Repository layout and dependency boundaries | Planned M0–M1 |
| ADR-0002 / ADR-0004 | Shadow/advisory only; no LLM or autonomous payment action in scoring | Configuration and later scoring implementation | Later / M2+ |

## Milestone gates

### Milestone 0 gate — complete locally

- [x] Backend/frontend directory structure exists.
- [x] Python and Node versions/package managers are pinned or explicitly documented.
- [x] Formatter, linter, type checker, unit-test runner, and CI workflow run on a clean checkout.
- [x] `.gitignore` excludes `.env`, generated data, caches, build output, and local database artifacts.
- [x] `.env.example` contains placeholders only.
- [x] Docker Compose defines the local API and PostgreSQL foundation; runtime start is pending Docker installation on this host.
- [x] README quick start and migration commands match the actual project, with migrations scheduled for M1.
- [x] License decision remains an explicit placeholder until resolved.

### Milestone 1 gate

- [x] FastAPI app starts with validated environment settings.
- [x] Request/correlation IDs are validated, propagated, and included in errors/log context.
- [x] Structured error envelope hides stack traces, SQL, and secrets.
- [x] PostgreSQL connectivity uses SQLAlchemy and migrations use Alembic.
- [x] Empty-database migration is defined and generated offline; live runtime verification is delegated to PostgreSQL CI because Docker is unavailable locally.
- [x] Liveness is dependency-independent; readiness checks the database and required configuration.
- [x] Tenant and API-key records are persisted with secure hashes, scopes, expiry, and revocation state.
- [x] Protected requests return 401 without credentials and 403 without required scope.
- [x] Auth-derived tenant context is required by tenant-owned access paths.
- [x] Cross-tenant isolation tests cover reads and writes.
- [x] Development bootstrap is explicitly local/test-only and never seeds production.

### Milestone 2 gate — complete locally

- [x] Canonical transaction schema validates integer minor units, ISO currency, timezone-aware timestamps, pseudonymous references, bounded metadata, and forbidden sensitive values.
- [x] Tenant-scoped transaction, assessment, signal, rule-set, and idempotency persistence exists with Alembic migration `0002_scoring`.
- [x] Deterministic versioned default rules produce explainable reason codes and evidence.
- [x] `POST /v1/transactions/score` requires `transactions:score` and returns shadow-mode assessments.
- [x] Same tenant/endpoint/idempotency key and same request fingerprint returns the original response.
- [x] Same idempotency key with a different request returns `409 IDEMPOTENCY_KEY_REUSED`.
- [x] Scores are constrained to 0–100 and no payment-decision operation exists.
- [x] M2 tests cover valid, invalid, unauthorized, idempotent, conflicting, bounded-score, and tenant-scoped behavior.

### Milestone 3 gate — complete locally

- [x] SDK exposes typed `Transaction` and `RiskAssessment` models.
- [x] SDK supports configurable base URL, API key, timeout, correlation IDs, and explicit idempotency keys.
- [x] SDK has typed authentication, validation, rate-limit, timeout, and server exceptions.
- [x] SDK performs no implicit retries and does not log credentials or raw payloads.
- [x] Synthetic merchant simulator demonstrates shadow mode and preserves its original outcome.
- [x] SDK contract tests cover success, authentication, validation, rate limit, and timeout paths.

### Milestone 4 gate — complete locally

- [x] High-risk assessments create one tenant-scoped alert with deterministic deduplication.
- [x] Alert list/detail routes enforce `cases:read` and pagination limits.
- [x] Alert status transitions, assignment, and disposition enforce `cases:write` and valid state transitions.
- [x] Bounded analyst notes are persisted and returned without raw credential handling.
- [x] Security-sensitive alert/case actions create redacted append-oriented audit records.
- [x] Audit reads enforce `audit:read` and tenant scope.
- [x] Transaction assessment history enforces `transactions:read` and tenant scope.

### Milestone 5 gate — complete locally

- [x] Synthetic scenarios use deterministic seeds and are explicitly labeled synthetic.
- [x] Feature extraction excludes scenario labels and post-event fields.
- [x] Temporal 80/20 holdout evaluation is reproducible.
- [x] Isolation Forest is behind a detector interface with version metadata.
- [x] Detector scores are documented as prioritization indices, not fraud probabilities.
- [x] Evaluation report includes prevalence, precision, recall, PR-AUC, confusion matrix, split, and limitations.
- [x] API continues to report ML disabled until an explicitly reviewed artifact is configured.

### Milestone 6 gate — complete locally

- [x] Next.js/TypeScript operations console builds successfully.
- [x] Console displays live API connection and shadow-mode state without seeded demo records.
- [x] Alert queue supports status filtering and selection.
- [x] Case detail displays score, reasons, detector/rule metadata, status control, and bounded analyst note interaction.
- [x] Dashboard does not include or persist an integration API key in browser assets.
- [x] Loading/error/empty concepts are represented by the dashboard state boundary; live OIDC/dashboard auth remains a later enterprise capability.

### Milestone 7 gate — complete locally

- [x] Request body size limits and bounded process-local rate limiting are configured.
- [x] Security response headers are applied.
- [x] Prometheus-compatible request count/duration metrics are exposed at `/metrics`.
- [x] Retention deletion service and local CLI are implemented for transactions, assessments/signals, alerts/notes, audit events, and idempotency records.
- [x] Retention behavior has tests and defaults are environment-configurable.
- [x] Reproducible latency probe and backup/restore runbook are present.
- [x] Dependency checks include pinned Python/npm dependencies and npm audit; live deployment scanning remains CI/host dependent.

### Milestone 8 gate — complete locally

- [x] Webhook endpoints and delivery attempts are persisted with tenant scope and idempotent event IDs.
- [x] Endpoint secrets are encrypted at rest and returned only during endpoint registration.
- [x] Deliveries use HMAC-SHA256 signatures with event ID, type, and timestamp headers.
- [x] Delivery failures use bounded exponential backoff and dead-letter status.
- [x] Replay is restricted to failed deliveries and creates an audit record.
- [x] SSRF-sensitive URL validation rejects non-HTTPS and private/local literal destinations.
- [x] Alert creation enqueues webhook work without performing network I/O in the scoring request.
- [x] Webhook signature, enqueue deduplication, success, and dead-letter tests pass.

- [x] Durable asynchronous event ingestion accepts tenant-scoped event IDs, returns 202, deduplicates duplicates, and has a bounded worker CLI.

### Milestone 9 gate — complete locally

- [x] Container runtime uses a non-root application user.
- [x] Customer-hosted deployment documents secret injection, PostgreSQL responsibility, network boundaries, migration order, backup, rollback, and health checks.
- [x] Configuration validation command does not print secret values.
- [x] Release checklist includes operational and deployment controls.
- [x] No cloud vendor or Kubernetes dependency was introduced.
- [x] Tenant rule configuration can be read and replaced as an audited, validated immutable version using `config:read`/`config:write`.

### Milestone 1 verification note

- Local unit/API/security tests pass: 12 tests.
- Offline Alembic SQL generation produces `tenants`, `api_keys`, `api_key_scopes`, and `audit_events`.
- CI now provisions PostgreSQL 16.4 and runs `python -m alembic upgrade head` before tests.
- Full PostgreSQL migration/bootstrap verification is pending because Docker and a usable local PostgreSQL instance are unavailable on the current host.

## Open decision register

These items should be resolved before the corresponding implementation slice makes them externally observable:

1. Idempotency conflict status: resolved in favour of `409 IDEMPOTENCY_KEY_REUSED`; API contract updated.
2. Development bootstrap surface: resolved with a local/test-only CLI that prints a key once; no admin API or dashboard auth is introduced.
3. API-key verification: resolved with high-entropy keys, a lookup prefix, server-side HMAC/SHA-256 hashing, constant-time comparison, expiry, and revocation. Rotation overlap remains a later control-plane feature.
4. Tenant isolation depth: application/service scoping is implemented. PostgreSQL row-level security remains a future higher-assurance/customer-hosted decision.
5. Audit timing: minimal bootstrap audit records are implemented; full credential/config/case audit coverage remains M4.
6. Runtime versions and tooling: resolved in M0 with Python 3.13, Node 24/npm 11, PostgreSQL 16.4, and pinned project dependencies.
7. Readiness dependencies: resolved for M1 as PostgreSQL and application configuration; ML remains disabled until M5.
8. Retention and pseudonymization: tenant-scoped HMAC pseudonymization is implemented for account/device references. Retention defaults exist in configuration, but deletion jobs remain M7 before any real pilot.
9. Database roles and migrations: least-privilege runtime/migration credentials are recommended but not specified for local Compose. Recommend separate documented roles where practical, with a simpler local profile explicitly limited to development.
