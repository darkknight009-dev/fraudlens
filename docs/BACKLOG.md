# Prioritized Backlog

Priority: P0 = required for first useful MVP; P1 = next; P2 = later enterprise capability.

## P0 — Integration-first foundation
- [ ] Repository structure and developer tooling
- [ ] Environment config and secret-safe `.env.example`
- [ ] Docker Compose for API + PostgreSQL
- [ ] FastAPI health/live and health/ready endpoints
- [ ] SQLAlchemy + Alembic
- [ ] Tenant and API key models
- [ ] Hashed API key storage and scopes
- [ ] Tenant context enforced in services/repositories
- [ ] Canonical transaction schema using amount_minor
- [ ] Request ID/correlation ID middleware
- [ ] Standard error envelope
- [ ] Idempotency record and fingerprinting
- [ ] Deterministic rules engine with versioned rules
- [ ] Risk aggregation (0–100 index, not probability)
- [ ] `POST /v1/transactions/score`
- [ ] Unit/integration/contract/security tests
- [ ] Python SDK with timeout and idempotency support
- [ ] Synthetic merchant simulator
- [ ] Shadow mode
- [ ] README quick start and sample request

## P1 — Investigation workflow and ML
- [ ] Persist risk signals and feature snapshots
- [ ] Alert/case deduplication
- [ ] Case status lifecycle and dispositions
- [ ] Analyst notes
- [ ] Audit log for security-sensitive actions
- [ ] Synthetic transaction generator with deterministic seed
- [ ] Feature engineering with point-in-time correctness
- [ ] Baseline anomaly detector
- [ ] Supervised classifier if suitable labels exist
- [ ] Evaluation report: precision, recall, PR-AUC, confusion matrix, FPR/FNR
- [ ] Model version metadata and safe fallback behavior
- [ ] React dashboard for transactions and cases
- [ ] Clear synthetic data and shadow-mode labels

## P1 — Operational hardening
- [ ] Rate limiting and payload limits
- [ ] Structured logs and redaction tests
- [ ] Retention/deletion job
- [ ] Metrics for latency/errors/scoring status
- [ ] Load test and report
- [ ] Backup/restore runbook
- [ ] CI dependency scanning
- [ ] OpenAPI contract verification

## P2 — Asynchronous integrations
- [ ] Durable event ingestion abstraction
- [ ] Queue worker and retry strategy
- [ ] HMAC-signed webhooks
- [ ] Webhook delivery attempts, dead-letter state, replay
- [ ] Provider-specific schema adapters
- [ ] Integration configuration wizard

## P2 — Customer-hosted/enterprise
- [ ] OIDC dashboard authentication
- [ ] RBAC for analyst/admin
- [ ] Container hardening and signed releases
- [ ] Customer-managed secrets
- [ ] Configuration export/import
- [ ] Rule/model rollback workflow
- [ ] Tenant-level retention configuration
- [ ] Operational SLOs and support docs
- [ ] Deployment/upgrade/rollback verification
