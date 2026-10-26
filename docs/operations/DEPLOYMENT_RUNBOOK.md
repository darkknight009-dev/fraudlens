# Deployment and Operations Runbook

## 1. Local development target
Prerequisites: supported Python version pinned in project config, Node LTS compatible with frontend tooling, Docker Desktop or Docker Engine, and Git.

Expected developer flow (commands should be adapted to actual implemented scripts):
```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose logs -f api
```
Provide a local seed command that creates a demo tenant and synthetic data. Never seed production environments with demo credentials.

## 2. Environment configuration
Maintain `.env.example` with placeholders for:
- `APP_ENV`
- `LOG_LEVEL`
- `DATABASE_URL`
- `API_KEY_HASH_PEPPER` (if used)
- `CORS_ALLOWED_ORIGINS`
- `RATE_LIMIT_*`
- `IDEMPOTENCY_TTL_SECONDS`
- `RISK_MODE_DEFAULT=shadow`
- `MODEL_ARTIFACT_PATH` (optional)
- `RETENTION_*`
- `WEBHOOK_*` only when implemented

Validate required settings on startup. Fail safely if a required production secret is missing. Never print secrets at startup.

## 3. Health checks
- Liveness: process is alive; no expensive external dependency checks.
- Readiness: database and required model/config are usable.
- Include version/build metadata but no secret/config dump.
- Use a graceful shutdown and bounded connection draining where deployment supports it.

## 4. Database operations
- Apply Alembic migrations as an explicit release step.
- Back up before production migrations.
- Test restore regularly.
- Index changes and large migrations require a documented plan.
- Use least-privilege DB roles; separate migration credentials from runtime credentials where feasible.

## 5. Observability
Log structured fields: timestamp, level, service, request_id, tenant pseudonymous ID, route, status, duration_ms, error_code. Do not log API keys, full transaction payloads, card data, or raw analyst notes.
Monitor:
- request count, latency, error rate
- 401/403/429 rate
- scoring status and detector failures
- database latency/pool saturation
- case creation rate
- model feature drift and score distribution when implemented

## 6. Failure playbooks
### Database unavailable
Readiness fails; return controlled service-unavailable response. Do not claim a normal assessment if persistence requirements are unmet.

### Model unavailable
If the tenant configuration explicitly allows rules-only degraded assessment, return `assessment_status=partial` and mark ML unavailable. Otherwise return a typed unavailable response. Never silently convert model failure into low risk.

### Webhook destination unavailable
Queue bounded retries; scoring response remains independent. Dead-letter after configured attempts and expose delivery status.

### API key compromised
Revoke key, issue replacement, inspect audit logs, check suspicious access, notify the tenant through agreed process, and document incident.

### Latency spike
Check dependency health, DB pool, feature-query patterns, model inference, and traffic. Apply rate limits and disable optional expensive detectors if the documented safe mode permits.

## 7. Deployment maturity
### MVP
Docker Compose, local database, synthetic data, development-only credentials.

### Pilot candidate
TLS, managed secrets, monitoring/alerting, backup/restore, retention/deletion, access control, load test, security review, incident response process, documented SLOs.

### Customer-hosted
Signed/versioned images, customer-managed secrets, upgrade/rollback procedure, network egress list, storage/retention configuration, backup responsibility matrix, migration procedure, health checks, and support policy.
