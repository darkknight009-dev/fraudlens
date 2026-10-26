# Product Requirements Document (PRD)

- Product: FraudLens
- Version: 0.1 (MVP)
- Status: Proposed
- Audience: Product, engineering, security, QA, future pilot customers

## 1. Executive summary
FraudLens is an integration-first fraud intelligence layer for fintech and payment platforms. It accepts normalized transaction events through a versioned API or asynchronous adapters, computes deterministic rule signals and ML-based risk signals, returns a transparent risk assessment, and helps analysts investigate suspicious activity. It is designed to integrate alongside existing systems rather than replace payment processing, authorization, or the customer's policy engine.

## 2. Problem statement
Organizations may operate transaction systems, fraud rules, and investigation tools that differ across products and channels. Integrating a new risk signal can require custom field mapping, operational safeguards, model monitoring, and investigation workflows. FraudLens aims to provide a consistent, documented interface and portable risk-intelligence capability.

This PRD does **not** assert that any named company has a specific internal defect or unmet need. Product hypotheses must be validated through research and pilot feedback.

## 3. Goals
1. Integrate a simulated merchant application in under 30 minutes using a documented API/SDK.
2. Normalize different transaction payloads into a canonical internal schema.
3. Return a deterministic, explainable risk assessment with reason codes.
4. Operate in shadow/advisory mode without affecting payment decisions.
5. Support tenant isolation, API-key rotation, audit records, and safe failure handling.
6. Establish an ML evaluation baseline using documented synthetic or public datasets.
7. Provide an analyst dashboard for alerts and case review.
8. Support local deployment using Docker Compose and document a path to customer-hosted deployment.

## 4. Non-goals for MVP
- Direct payment authorization, capture, settlement, refund, or money movement.
- Automatic transaction blocking or customer punishment.
- Claiming production-grade fraud detection or a guaranteed detection rate.
- Processing cardholder data such as PAN, CVV, PIN, or authentication secrets.
- A universal plug-in that works with every fintech product without configuration.
- Native connectors for every vendor.
- Autonomous agent decisions on financial outcomes.
- Kubernetes/microservices as a prerequisite for MVP.
- Training on real customer data without explicit authorization, governance, and legal review.

## 5. Personas
### Integration engineer
Needs a stable API, SDK, clear schemas, idempotency, example code, versioning, and predictable error behavior.

### Fraud/risk analyst
Needs prioritized alerts, traceable reasons, transaction context, case notes, and an auditable review outcome.

### Platform/SRE engineer
Needs health/readiness endpoints, latency/error metrics, timeouts, retry guidance, logs, and deployment controls.

### Security/compliance reviewer
Needs minimal data collection, access control, tenant separation, auditability, retention controls, and documented threat assumptions.

### ML engineer
Needs reproducible datasets, leakage-resistant splits, versioned models, evaluation metrics, and drift monitoring.

## 6. User journeys
1. Admin creates a tenant and an integration credential.
2. Engineer runs the sample app and sends a test transaction.
3. FraudLens validates and normalizes the event.
4. Rule engine and, when enabled, ML detector produce signals.
5. Risk aggregation returns score, level, reason codes, versions, and correlation ID.
6. In shadow mode, the merchant records the result but continues its original decision path.
7. High-priority signals create an alert/case according to tenant configuration.
8. Analyst reviews evidence, records disposition, and adds a note.
9. Admin checks integration health and exports evaluation/report data.

## 7. Functional requirements
### FR-01: Tenant-aware authentication
All customer-facing API operations must authenticate the caller and resolve a tenant context. API keys must be stored hashed, scoped, revocable, and rotatable. Do not accept a tenant ID from request bodies as authority.

### FR-02: Canonical transaction schema
Support transaction reference, amount, currency, event time, account/customer pseudonymous reference, device reference, merchant reference, channel, status, and optional provider metadata. Define required/optional fields and validation rules in the API contract.

### FR-03: Schema adapters
Map external payload fields to canonical fields using explicit, validated configuration. Unknown fields must not silently become trusted signals.

### FR-04: Scoring API
Provide a versioned endpoint returning risk score (0–100), risk level, reason codes, assessment ID, rule/model versions, scoring mode, and correlation ID.

### FR-05: Rule engine
Provide configurable, versioned rules. Rules must be deterministic, explainable, testable, and tenant-scoped. Thresholds are examples, not universal fraud indicators.

### FR-06: ML detector
Provide a pluggable detector interface. Start with an unsupervised baseline such as Isolation Forest on carefully scaled features. Do not treat anomaly score as calibrated fraud probability. Add supervised classification only with appropriate labels and leakage-resistant evaluation.

### FR-07: Shadow mode
In shadow mode, scores and alerts must not alter authorization, settlement, or payment outcomes. This is the default mode and must be clearly shown in UI and API responses.

### FR-08: Alerts and cases
Create an alert/case for configured risk conditions. Support list/detail, assignment (optional MVP), status transitions, notes, and final analyst disposition. Prevent duplicate cases from duplicate event submissions.

### FR-09: Webhooks
Later milestone: deliver signed webhooks with retries, idempotent event IDs, delivery logs, and a replay mechanism. Do not block synchronous scoring on webhook delivery.

### FR-10: Audit log
Record authentication/credential events, configuration changes, rule/model version changes, scoring decisions, case status transitions, and exports. Avoid storing unnecessary raw sensitive payloads.

### FR-11: Observability
Expose liveness/readiness, structured logs, request correlation IDs, latency/error metrics, and basic operational dashboards.

### FR-12: Data retention
Provide configurable retention policy for transaction payloads, feature records, alerts, and audit logs. MVP must document defaults and implement deletion/retention jobs before any real pilot.

### FR-13: Dashboard
Provide transaction search, alert list, case detail, score/reasons, filter by date/risk/status, and basic aggregate charts.

### FR-14: SDK and sample integration
Provide a Python SDK and sample merchant simulator that demonstrate authentication, score request, timeout handling, idempotency, and shadow mode.

## 8. Non-functional requirements
- Security: authenticated access, tenant isolation, least privilege, secrets hygiene, input validation, secure defaults.
- Reliability: bounded request timeouts, explicit failure states, health checks, safe retries, idempotency.
- Performance target for local MVP: define and measure p50/p95 scoring latency under a documented synthetic load; initial engineering target p95 < 200 ms for deterministic scoring on local development hardware, excluding network and dashboard. This is a target to validate, not a guarantee.
- Availability: no production SLA is claimed for MVP.
- Scalability: stateless API workers where possible; persistence and feature processing must be separable.
- Maintainability: typed interfaces, migrations, tests, docs, reproducible local setup.
- Explainability: every risk signal must cite reason code, relevant feature/rule, and version.
- Portability: Docker Compose local deployment; environment-driven configuration.
- Accessibility: dashboard controls should be keyboard navigable and have meaningful labels.

## 9. Success metrics
- Integration time for sample app: <= 30 minutes following docs.
- API contract tests: 100% of documented contract cases pass.
- No cross-tenant data access in automated security tests.
- Deterministic rule output reproducible for identical inputs/configuration.
- Documented precision, recall, PR-AUC where appropriate, false-positive rate, and confusion matrix on a held-out dataset.
- p50/p95/p99 latency and error rate reported under defined load.
- Analyst can review and disposition an alert end-to-end.
- Shadow mode has no code path that changes payment outcomes.

## 10. Risks and mitigations
- Poor labels or class imbalance: report appropriate metrics; use temporal/group splits; disclose dataset limits.
- Data leakage: split by time/account as appropriate; fit preprocessing only on training data.
- False positives: human review, threshold tuning, monitor precision and review burden.
- Integration complexity: canonical schema, adapters, SDK, sample app, contract tests.
- Service failure: timeouts, circuit breakers at integration edge, explicit degraded state.
- Sensitive data exposure: data minimization, synthetic defaults, redaction, tenant isolation.
- Overclaiming: label all demo data as synthetic and distinguish benchmark results from production performance.

## 11. Release gates
No real-company pilot until security review, threat model review, retention implementation, backup/restore test, load test, access control review, model evaluation review, incident runbook, and explicit customer approval are complete.
