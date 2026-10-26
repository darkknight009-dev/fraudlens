# Test Strategy

## 1. Testing layers
### Unit tests
- Canonical schema validation and normalization.
- Currency/amount/time validation.
- Feature calculations and missing-value behavior.
- Rule evaluation and threshold boundaries.
- Risk aggregation and reason-code generation.
- Idempotency fingerprinting.
- Case state transitions.
- API key hashing, scopes, and expiry.

### Integration tests
- API + PostgreSQL persistence.
- Assessment + signals transaction consistency.
- Duplicate request behavior.
- Tenant scoping across all read/write operations.
- Rule-set activation and rollback.
- Health/readiness behavior when dependencies are unavailable.
- Alert deduplication.
- Migration from empty database to latest schema.

### Contract tests
- Request/response schema matches API documentation/OpenAPI.
- Python SDK behavior matches server contract.
- Backward compatibility for the current `/v1` schema.
- Error envelope and status-code behavior.

### Security tests
- Missing/invalid/revoked/expired API keys.
- Scope violations.
- Cross-tenant IDOR attempts.
- Oversized payloads and invalid metadata.
- Injection strings.
- Sensitive-value log redaction.
- Rate-limit behavior.
- Webhook signature/replay tests when webhooks exist.

### ML tests
- Deterministic preprocessing and fixed random seeds.
- No target leakage.
- Train/test split reproducibility.
- Feature schema compatibility.
- Metrics computed on held-out data.
- Model artifact version validation.
- Missing/shifted feature handling.
- Threshold selection documented.
- Compare rule baseline, anomaly baseline, and supervised model when labels permit.

### End-to-end tests
- Merchant simulator sends transaction and receives assessment.
- Shadow mode does not alter simulator's original outcome.
- Analyst opens alert, adds note, and resolves it.
- SDK handles timeout, 401, 422, 429, and 5xx safely.

## 2. Required metrics
For classifier: precision, recall, F1 where useful, PR-AUC, confusion matrix, false-positive rate, false-negative rate, and threshold rationale. ROC-AUC may be supplementary but should not be the only metric for imbalanced data.

For anomaly detection: use labeled holdout if available; otherwise report ranking/inspection methodology and do not claim fraud accuracy.

For service: p50/p95/p99 latency, throughput, error rate, queue delay if applicable, CPU/memory, and database query performance.

## 3. Dataset discipline
- Label all synthetic data clearly.
- Use deterministic seeds.
- Separate generation rules from detector logic.
- Split data by time and/or account/entity to reduce leakage.
- Do not put synthetic labels or scenario IDs into model features.
- Keep test fixture datasets small and safe to commit.
- Document dataset source, license, limitations, and class prevalence.

## 4. CI gate
A pull request should run:
1. formatting/lint
2. type checking
3. unit tests
4. integration tests using a disposable test database
5. API schema generation/contract checks
6. dependency/security scan where available
7. frontend tests/build when frontend exists

Never suppress a failing test without documenting the reason and follow-up issue.
