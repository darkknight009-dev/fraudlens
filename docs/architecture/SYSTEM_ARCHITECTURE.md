# System Architecture

## 1. Architecture principles
- Modular monolith first; split services only for demonstrated scaling/ownership needs.
- API and event adapters are separate from detection logic.
- Canonical transaction schema is the internal contract.
- Deterministic rules and ML detectors return typed signals; a risk aggregator creates the assessment.
- Customer policy engine remains authoritative.
- Default behavior is advisory/shadow mode.
- Tenant identity comes from authenticated credentials, never request-supplied tenant fields.
- Store money as integer minor units or Decimal, never binary float.
- All timestamps are timezone-aware and stored in UTC.

## 2. Logical components
1. **API edge:** FastAPI routes, auth, request validation, rate limits, correlation IDs.
2. **Integration adapters:** external-to-canonical schema mapping; provider-specific parsing.
3. **Transaction service:** idempotent ingestion and persistence.
4. **Feature service:** deterministic feature calculations from available history.
5. **Rules engine:** versioned, tenant-scoped configurable rules.
6. **Detector interface:** baseline ML model and future model implementations.
7. **Risk aggregator:** maps evidence to a 0–100 risk score and level; exposes reason codes and version metadata.
8. **Alert/case service:** case creation, analyst workflow, disposition.
9. **Audit service:** append-oriented records for security-sensitive actions.
10. **Webhook dispatcher (later milestone):** signed asynchronous event delivery and retries.
11. **Dashboard:** React client consuming public API.
12. **Operations:** health/readiness, metrics, logs, migrations, backups, retention.

## 3. Suggested repository layout
```text
fraudlens/
  AGENTS.md
  README.md
  pyproject.toml
  .env.example
  docker-compose.yml
  Dockerfile
  backend/
    app/
      main.py
      api/v1/
      core/             # settings, auth, errors, logging
      db/               # session, base, migrations
      models/           # ORM entities
      schemas/           # Pydantic request/response schemas
      repositories/
      services/
        ingestion.py
        features.py
        rules.py
        detectors/
        scoring.py
        alerts.py
        cases.py
        audit.py
      adapters/
      workers/           # future async workers
    tests/
      unit/
      integration/
      contract/
      security/
  sdk/python/
  examples/merchant_simulator/
  frontend/
  data/
    synthetic/           # generated; do not commit sensitive data
  scripts/
  docs/
```
The agent may refine this layout but must document deviations.

## 4. Core scoring flow
1. Authenticate caller and resolve tenant.
2. Validate payload against versioned Pydantic schema.
3. Check idempotency key and request fingerprint.
4. Normalize fields and validate currency/amount/time.
5. Persist transaction or resolve existing idempotent result.
6. Compute deterministic features available at decision time.
7. Evaluate enabled rules and optional detector.
8. Aggregate evidence into score and risk level.
9. Persist assessment and associated reason codes/model/rule versions.
10. Create case/alert only when configured and not duplicated.
11. Return assessment with correlation ID.
12. Emit async events later; webhook failures must not change scoring response.

## 5. Risk score semantics
- Score range: integer 0–100.
- `risk_level`: `low`, `medium`, `high`, `critical` based on tenant-configurable thresholds with safe defaults.
- Score is a prototype prioritization index, not a fraud probability.
- Every signal includes a stable `reason_code`, human-readable message, severity/contribution, and evidence fields that do not expose sensitive data.
- The aggregation function must be deterministic for identical feature values, rule/model versions, and configuration.
- Missing features must be explicit; never silently interpret missing data as safe.
- If model is unavailable, return the documented degraded state and continue with rules only only when tenant policy allows. The result must clearly indicate detector status.

## 6. Storage boundaries
- PostgreSQL stores tenant config, credential metadata, transaction metadata, assessments, reason codes, cases, audit records, and webhook delivery state.
- Never store raw card credentials or sensitive authentication data.
- Raw provider payload storage is off by default; if enabled later, require allowlisted fields, encryption, retention, and review.
- Feature history must be tenant-scoped and have a documented retention period.

## 7. Deployment topology
### Local MVP
Docker Compose: API, PostgreSQL, optional Redis, frontend. Database migration runs as an explicit command/entrypoint step, not ad-hoc on every app import.

### Hosted SaaS later
Load balancer/API service, managed PostgreSQL, secrets manager, centralized logs/metrics, optional managed queue, object storage only if justified, backups and restore drills.

### Customer-hosted later
Container images, customer-managed secrets/database, configuration guide, health checks, migrations, data retention controls, outbound network requirements, and signed release artifacts.

## 8. Availability and failure handling
- Configure connect/read timeouts for downstream calls.
- Synchronous scoring must not depend on webhook success.
- Use bounded retries only for safe/idempotent operations.
- Include `assessment_status` such as `complete`, `partial`, or `unavailable`; do not disguise failed model execution as a normal result.
- Circuit breakers belong in integrations/downstream clients where appropriate.
- Define merchant-side behavior for timeout and service outage; FraudLens does not make that choice automatically.
- No hidden fail-open/fail-closed decision. Any failure policy must be explicit, documented, and customer-controlled.

## 9. Future scaling triggers
Consider a separate worker or service only when metrics show need: high event volume, long-running model inference, queue backlog, independent release cadence, or tenant isolation requirements. Do not add Kafka/Kubernetes before a measurable requirement.
