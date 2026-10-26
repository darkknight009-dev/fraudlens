# Prioritized Backlog

Priority: P0 = required for first useful MVP; P1 = next; P2 = later enterprise capability.

## P0 — Integration-first foundation — complete
- [x] Repository structure and developer tooling
- [x] Environment config and secret-safe `.env.example`
- [x] Docker Compose for API + PostgreSQL
- [x] FastAPI health/live and health/ready endpoints
- [x] SQLAlchemy + Alembic
- [x] Tenant and API key models
- [x] Hashed API key storage and scopes
- [x] Tenant context enforced in services/repositories
- [x] Canonical transaction schema using amount_minor
- [x] Request ID/correlation ID middleware
- [x] Standard error envelope
- [x] Idempotency record and fingerprinting
- [x] Deterministic rules engine with versioned rules
- [x] Risk aggregation (0–100 index, not probability)
- [x] `POST /v1/transactions/score`
- [x] Unit/integration/contract/security tests
- [x] Python SDK with timeout and idempotency support
- [x] Synthetic merchant simulator
- [x] Shadow mode
- [x] README quick start and sample request

## P1 — Investigation workflow and ML — complete
- [x] Persist risk signals and feature snapshots
- [x] Alert/case deduplication
- [x] Case status lifecycle and dispositions
- [x] Analyst notes
- [x] Audit log for security-sensitive actions
- [x] Synthetic transaction generator with deterministic seed
- [x] Feature engineering with point-in-time correctness
- [x] Baseline anomaly detector
- [x] Supervised classifier if suitable labels exist
- [x] Evaluation report: precision, recall, PR-AUC, confusion matrix, FPR/FNR
- [x] Model version metadata and safe fallback behavior
- [x] Next.js operations console for live transactions and cases
- [x] Explicit shadow-mode label with no fabricated console data

## P1 — Operational hardening — complete
- [x] Rate limiting and payload limits
- [x] Structured logs and redaction tests
- [x] Retention/deletion job
- [x] Metrics for latency/errors/scoring status
- [x] Load test and report
- [x] Backup/restore runbook
- [x] CI dependency scanning
- [x] OpenAPI contract verification

## P2 — Asynchronous integrations — complete
- [x] Durable event ingestion abstraction
- [x] Queue worker and retry strategy
- [x] HMAC-signed webhooks
- [x] Webhook delivery attempts, dead-letter state, replay
- [ ] Provider-specific schema adapters
- [ ] Integration configuration wizard

## P2 — Customer-hosted/enterprise — deployment profile complete; enterprise identity features pending
- [ ] OIDC dashboard authentication
- [ ] RBAC for analyst/admin
- [x] Container hardening and signed releases
- [x] Customer-managed secrets
- [ ] Configuration export/import
- [ ] Rule/model rollback workflow
- [x] Tenant-level retention configuration
- [x] Operational SLOs and support docs
- [x] Deployment/upgrade/rollback verification
