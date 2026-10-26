# FraudLens Requirements-to-Implementation Traceability

**Baseline date:** 2026-10-26  
**Implementation status:** Milestone 0 complete; Milestone 1 not started.

## Current repository state

The repository currently contains the product, architecture, API, security, testing, operations, ADR, backlog, and milestone documentation. It does not yet contain:

- Python or frontend package configuration
- FastAPI application code
- PostgreSQL/SQLAlchemy models or Alembic migrations
- Docker Compose or application Dockerfiles
- CI workflow, formatter, linter, type-check, or test configuration
- Python SDK or merchant simulator
- React dashboard or generated OpenAPI contract checks

## Traceability checklist

Status values: `Not started`, `Planned M0`, `Planned M1`, `Later`, and `Needs decision`.

| Requirement / source | Acceptance evidence | Implementation target | Status |
|---|---|---|---|
| PRD FR-01; Security §3; ADR-0002 | Authenticated caller resolves tenant; missing, invalid, expired, and revoked keys fail safely; scopes are enforced | API-key model, auth dependency, tenant context, scope dependency, security tests | Planned M1 |
| PRD FR-02; Integration §2; ADR-0003 | Canonical fields and validation are documented and represented by typed schemas | Versioned Pydantic transaction schema and validation tests | Planned M2 |
| PRD FR-03; Integration §3 | Explicit mappings validate before activation; unknown fields are dropped | Adapter/mapping module and configuration validation | Later / M2+ |
| PRD FR-04; API §32–89 | Versioned scoring response includes score, level, mode, status, signals, versions, detector status, and request ID | `/v1/transactions/score` and contract tests | Later / M2 |
| PRD FR-05; Architecture §18–21 | Tenant-scoped, versioned deterministic rules produce traceable signals | Rule configuration, evaluator, and aggregation service | Later / M2 |
| PRD FR-06; ML Governance; ADR-0004 | Detector is behind an interface; evaluation prevents leakage and does not call anomaly score a probability | Detector interface and evaluation pipeline | Later / M5 |
| PRD FR-07; Integration §7; ADR-0002 | Shadow is the default and no FraudLens code path changes payment outcomes | Mode configuration, response field, simulator proof | Later / M2–M3 |
| PRD FR-08; Data Model §65–82 | Alert/case lifecycle, deduplication, notes, dispositions, and tenant isolation work | Alert/case service and API | Later / M4 |
| PRD FR-09; Integration §9 | Signed, retried, replayable webhooks do not block scoring | Webhook dispatcher and delivery store | Later / M8 |
| PRD FR-10; Data Model §94–103; Security §6 | Security-sensitive actions create append-oriented redacted audit events | Audit service and audit API | Later / M4 |
| PRD FR-11; API §25–30; Runbook §3–5 | Liveness, readiness, correlation IDs, structured logs, and operational signals are available | Health routes, middleware, logging, initial metrics hooks | Planned M1; hardening later |
| PRD FR-12; Security §2 | Retention defaults are documented and deletion is tested before real pilot use | Retention configuration/job and tests | Later / M7 |
| PRD FR-13 | Analyst dashboard supports transaction, alert, case, and score workflows | React dashboard | Later / M6 |
| PRD FR-14; Integration §8 | Typed SDK and simulator demonstrate auth, timeout, idempotency, and shadow behavior | Python SDK and merchant simulator | Later / M3 |
| NFR security; Security §2–3 | No payment credentials; secrets are hashed/rotated; input and tenant boundaries are protected | Secret-safe config, validation, auth, isolation tests | Planned M0–M1; hardening later |
| NFR reliability; Architecture §111–118 | Bounded dependencies, explicit readiness/failure states, and no hidden payment decision | Health/readiness and failure policy | Planned M1; scoring later |
| NFR performance; PRD §110, §124 | Synthetic load reports p50/p95/p99 latency and error rate | Load test and report | Later / M7 |
| NFR maintainability/portability; M0 | Fresh setup, pinned dependencies, Docker Compose, migrations, checks, and CI are reproducible | Project tooling and local runtime | M0 complete; Docker runtime pending host availability |
| API §1–23 | `/v1` conventions, UTC timestamps, safe error envelope, and request ID are consistent | Settings, middleware, exception handlers, API tests | Planned M1 |
| API §26–30 | Live endpoint does not require DB; ready endpoint checks required dependencies and returns safe 503 | `/health/live`, `/health/ready` | Planned M1 |
| API §32–99 | Scoring auth, validation, idempotency, status codes, and degraded behavior match contract | Scoring route/service and contract tests | Later / M2 |
| API §102–124 | Tenant-scoped pagination, case/config/audit permissions, and transitions are enforced | Later API routes and repository tests | Later / M4 |
| Data Model §1–126; ADR-0005 | PostgreSQL tables, constraints, UTC timestamps, indexes, and tenant-scoped queries migrate from empty DB | Initial metadata plus tenant/API-key migrations; remaining entities by milestone | Planned M1 |
| Testing Strategy §1–80 | Unit, integration, contract, security, and CI checks run and report actual results | Test layout and CI gates | M0 foundation complete; expanded later |
| Implementation Plan M0 | Clean install instructions, ignored secrets/generated data, and basic CI checks work | Project skeleton and developer tooling | M0 complete; Compose runtime pending host availability |
| Implementation Plan M1 | Empty-DB migration works; health checks work; protected requests return 401; scopes and isolation are tested | FastAPI foundation, DB, auth, tenant context | Planned M1 |
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

- [ ] FastAPI app starts with validated environment settings.
- [ ] Request/correlation IDs are validated, propagated, and included in errors/log context.
- [ ] Structured error envelope hides stack traces, SQL, and secrets.
- [ ] PostgreSQL connectivity uses SQLAlchemy and migrations use Alembic.
- [ ] Empty database migrates successfully.
- [ ] Liveness is dependency-independent; readiness checks the database and required configuration.
- [ ] Tenant and API-key records are persisted with secure hashes, scopes, expiry, and revocation state.
- [ ] Protected requests return 401 without credentials and 403 without required scope.
- [ ] Auth-derived tenant context is required by tenant-owned access paths.
- [ ] Cross-tenant isolation tests cover reads and writes.
- [ ] Development bootstrap is explicitly local/development-only and never seeds production.

## Open decision register

These items should be resolved before the corresponding implementation slice makes them externally observable:

1. Idempotency conflict status: API §94 lists `400`, while API §131 specifies `409 IDEMPOTENCY_KEY_REUSED`. Recommend `409` and update the contract before M2.
2. Development bootstrap surface: no admin API or dashboard auth is defined for M1. Recommend a local-only CLI/one-shot command that prints a key once and is disabled when `APP_ENV` is non-development.
3. API-key verification: the documents require hashed keys but do not select an algorithm or pepper policy. Recommend high-entropy random keys with a lookup prefix and a server-side HMAC/pepper hash, constant-time verification, expiry, revocation, and rotation overlap; record the choice in an ADR.
4. Tenant isolation depth: application/service scoping is mandatory, but database row-level security is not decided. Recommend explicit repository/service scoping for M1, with an ADR on PostgreSQL RLS before customer-hosted or higher-assurance deployment.
5. Audit timing: FR-10 and Security §6 require credential/security auditing, while the milestone plan schedules the audit service for M4. Recommend recording minimal API-key bootstrap/revocation/security events in M1, then expanding the audit model in M4.
6. Runtime versions and tooling: Python, Node, PostgreSQL, package managers, formatter, linter, and type checker are not specified. Recommend pinning supported versions in project configuration during M0.
7. Readiness dependencies: the runbook mentions required model/config, but ML is later. Recommend M1 readiness checks PostgreSQL and required application configuration only; treat ML as disabled until M5.
8. Retention and pseudonymization: the data model permits either hashes or pseudonymous references, but the canonical reference strategy and default retention periods are not selected. Recommend deterministic tenant-scoped HMAC pseudonyms and document retention before any real pilot; do not block synthetic M1 work on this.
9. Database roles and migrations: least-privilege runtime/migration credentials are recommended but not specified for local Compose. Recommend separate documented roles where practical, with a simpler local profile explicitly limited to development.
