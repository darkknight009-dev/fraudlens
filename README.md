# FraudLens — Build Documentation

**Purpose:** Source-of-truth documentation for building FraudLens from scratch as an integration-first, deployable fraud intelligence platform.

**Status:** MVP specification. This describes a prototype designed for realistic integration and evaluation; it is not a claim of production certification or guaranteed fraud detection performance.

## Product summary
FraudLens is a fraud-risk intelligence layer that integrates with existing fintech systems through a synchronous REST API, asynchronous event/webhook patterns, and eventually customer-hosted deployment. It normalizes transaction data, evaluates configurable rules and ML signals, returns explainable risk assessments, and supports human investigation. It must not independently move money, authorize payments, or block transactions by default.

## Read these documents in order
1. [`AGENTS.md`](AGENTS.md) — mandatory instructions for coding agents.
2. [`docs/product/PRD.md`](docs/product/PRD.md) — product requirements.
3. [`docs/architecture/SYSTEM_ARCHITECTURE.md`](docs/architecture/SYSTEM_ARCHITECTURE.md) — architecture and boundaries.
4. [`docs/architecture/INTEGRATION_DESIGN.md`](docs/architecture/INTEGRATION_DESIGN.md) — integration modes and SDK strategy.
5. [`docs/api/API_CONTRACT.md`](docs/api/API_CONTRACT.md) — API conventions and endpoint contract.
6. [`docs/architecture/DATA_MODEL.md`](docs/architecture/DATA_MODEL.md) — entities and persistence.
7. [`docs/security/SECURITY_PRIVACY.md`](docs/security/SECURITY_PRIVACY.md) — security and privacy requirements.
8. [`docs/testing/TEST_STRATEGY.md`](docs/testing/TEST_STRATEGY.md) — verification strategy.
9. [`docs/operations/DEPLOYMENT_RUNBOOK.md`](docs/operations/DEPLOYMENT_RUNBOOK.md) — local and deployment operations.
10. [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) — milestone order and acceptance criteria.
11. [`docs/BACKLOG.md`](docs/BACKLOG.md) — prioritized implementation backlog.
12. [`docs/DEFINITION_OF_DONE.md`](docs/DEFINITION_OF_DONE.md) — completion bar.
13. [`docs/DEMO_PLAN.md`](docs/DEMO_PLAN.md) — synthetic demo flow.
14. [`docs/adr/`](docs/adr/) — architectural decision records.

## Non-negotiable product principles
- Integration-first: API contract, SDK, sample merchant integration, and shadow mode come before dashboard polish.
- Human decision authority: FraudLens provides risk intelligence; the integrating company's policy engine remains the decision-maker.
- Safe defaults: scoring is advisory; no real payments are initiated, rejected, or altered by FraudLens.
- Privacy by design: use synthetic data by default; never collect PAN, CVV, PIN, passwords, or payment credentials.
- Explainability: return reason codes and model/rule versions, not unsupported natural-language claims.
- Resilience: bounded timeouts, idempotency, health checks, structured logs, and explicit failure behavior.
- Measurability: evaluate precision, recall, PR-AUC where appropriate, false-positive rate, calibration where relevant, and latency. Never report accuracy alone.
- Portable deployment: local Docker Compose first; keep core components containerizable for future customer-hosted deployment.

## Current scope
The initial MVP is a modular monolith with FastAPI, PostgreSQL, SQLAlchemy/Alembic, Pydantic, scikit-learn, pytest, Docker Compose, and a small React + TypeScript dashboard. Async messaging and advanced enterprise deployment are staged later.

## How to use with a coding agent
Start a fresh agent session by asking it to read `AGENTS.md` and all documents in the order above. Ask it to implement one milestone at a time. It must inspect the repository before editing, summarize a plan, implement tests, run available checks, and update docs. It must not silently skip acceptance criteria or claim commands passed unless actually run.

## Local development

Milestone 0 establishes the project foundation. The API scaffold requires Python 3.13 and the dashboard scaffold requires Node 24/npm 11. Docker Desktop or Docker Engine is required for the PostgreSQL Compose environment.

```bash
cp .env.example .env
python3 -m pip install -e ".[dev]"
npm --prefix frontend ci
docker compose up --build -d
make check
```

The current API scaffold is available at `http://localhost:8000/`. Database migrations, health/readiness endpoints, authentication, and tenant persistence are Milestone 1 work. Do not use the development Compose credentials or synthetic scaffold with real customer or payment data.

See [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md) for milestone gates and unresolved decisions.
