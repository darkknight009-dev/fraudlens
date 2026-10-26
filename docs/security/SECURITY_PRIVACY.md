# Security, Privacy, and Threat Model

## 1. Security posture
This MVP is a development prototype, not certified production software. Do not connect to real payment rails or ingest real customer data until a security review and release gates are satisfied.

## 2. Data minimization
- Use synthetic data by default.
- Never collect/store PAN, CVV, PIN, OTP, passwords, bank login credentials, or authentication secrets.
- Use pseudonymous account/device references; hash or tokenize where practical.
- Allowlist metadata fields and enforce payload size limits.
- Avoid retaining raw payloads by default.
- Redact logs, exception traces, audit details, and analytics exports.
- Document retention periods and implement deletion before any real pilot.

## 3. Authentication and authorization
- Integration keys must be random, high entropy, shown once, hashed at rest, scoped, revocable, expiring, and rotatable.
- Use constant-time comparison where applicable.
- Never expose integration secrets in frontend bundles.
- Dashboard user authentication should use a standard OIDC provider in a later milestone; local demo auth must be explicitly marked as development-only.
- Enforce tenant scoping in repositories and services, not only UI.
- Rate-limit authentication failures and expensive endpoints.

## 4. Threats and mitigations
| Threat | Mitigation |
|---|---|
| Cross-tenant data exposure | Tenant context from auth, scoped queries, database constraints, isolation tests |
| API key theft | Hash keys, show once, rotation/revocation, scopes, rate limits, secret manager |
| Replay/duplicate requests | Idempotency keys, request fingerprints, event IDs |
| Malicious oversized payload | Request size limits, schema validation, bounded strings/lists |
| Injection | Parameterized queries/ORM, output encoding, dependency updates |
| Sensitive logs | Structured redaction, logging tests, no raw payload dumps |
| Model manipulation/data poisoning | Versioned models, controlled training pipeline, data provenance |
| False positives | Human review, transparent reasons, thresholds and evaluation |
| Service outage | Timeouts, health checks, circuit breakers at client edge, degraded state |
| Webhook spoof/replay | HMAC signatures, timestamp tolerance, replay prevention |
| SSRF via webhook URLs | Egress allowlist, block private/link-local ranges, DNS/IP revalidation, redirect controls |
| Unauthorized config changes | Scopes/RBAC, audit, validation, rollback |
| Prompt injection against future LLM | Treat evidence as data, no tool authority, constrained summaries, output validation |

## 5. Model governance
- Track model version, training data provenance, feature list, training timestamp, evaluation results, and intended use.
- Split train/test by time and/or entity where leakage is plausible.
- Do not train on labels that were not available at decision time.
- Report precision, recall, PR-AUC where appropriate, false-positive rate, confusion matrix, and threshold selection rationale.
- Explain model limitations and dataset limitations in the UI/docs.
- No LLM controls risk score or payment action.
- Do not call a score a probability unless it is calibrated and calibration is evaluated.

## 6. Audit requirements
Audit API-key creation/revocation, login/security events, rule/model activation, configuration changes, alert transitions, analyst dispositions, exports, and admin actions. Audit entries should be append-oriented and protected from routine edits.

## 7. Secure development
- Pin dependencies and scan for known vulnerabilities in CI.
- Use least-privilege database credentials.
- Keep secrets in `.env` locally only; `.env` is gitignored.
- Commit `.env.example` with placeholders only.
- Use non-root containers where practical.
- Keep CORS allowlists explicit.
- Do not enable debug mode in deployed environments.
- Use TLS in any non-local environment.
- Review license and supply-chain implications of dependencies.

## 8. Pilot readiness checklist
- Threat model reviewed.
- Tenant isolation verified.
- Auth scopes and key rotation tested.
- Retention and deletion tested.
- Backups and restore tested.
- Load and failure testing complete.
- Incident response contact/process defined.
- Model evaluation reviewed.
- Customer data-flow and legal review complete.
- Explicit customer approval for each integration and data field.
