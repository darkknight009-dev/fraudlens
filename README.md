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
The initial MVP is a modular monolith with FastAPI, PostgreSQL, SQLAlchemy/Alembic, Pydantic, scikit-learn, pytest, Docker Compose, and a Next.js operations console. The console uses live API data only; it does not ship seeded alerts or demo records. Async messaging and advanced enterprise deployment are staged later.

## How to use with a coding agent
Start a fresh agent session by asking it to read `AGENTS.md` and all documents in the order above. Ask it to implement one milestone at a time. It must inspect the repository before editing, summarize a plan, implement tests, run available checks, and update docs. It must not silently skip acceptance criteria or claim commands passed unless actually run.

## Local development

The project foundation and API skeleton require Python 3.13; the dashboard scaffold requires Node 24/npm 11. Docker Desktop or Docker Engine is required for the PostgreSQL Compose environment.

```bash
cp .env.example .env
python3 -m pip install -e ".[dev]"
python3 -m pip install -e sdk/python
npm --prefix frontend ci
docker compose up --build -d
make check
```

The API is available at `http://localhost:8000/`. Apply the database migration explicitly after the services start:

If host port `5432` is already in use, set `POSTGRES_HOST_PORT=5433` in `.env`; the API still connects to PostgreSQL internally on port `5432`.

```bash
docker compose exec api python -m alembic upgrade head
docker compose exec api python -m app.cli.bootstrap --scope transactions:score
```

The API exposes `/health/live` and `/health/ready`. The bootstrap command is development/test-only and displays the integration key once. Do not use the development Compose credentials or synthetic scaffold with real customer or payment data.

### Next.js operations console

Configure the live dashboard through a server-only environment file. The API key must not use a `NEXT_PUBLIC_` prefix and is never sent to browser JavaScript:

```bash
cp frontend/.env.local.example frontend/.env.local
# Set FRAUDLENS_DASHBOARD_API_KEY to the key printed by bootstrap.
npm run dev --prefix frontend
```

Open `http://localhost:3000`. The console starts empty when the API has no alerts; it never fabricates rows or metrics. Next.js proxies authenticated requests to the FastAPI API through server route handlers.

The console sections are live API surfaces: Overview and Alert queue read cases, Transactions looks up or scores canonical transactions, Rules reads/publishes versioned rule configuration, Audit trail reads tenant audit events, and Webhooks registers endpoints/replays failed deliveries. The bootstrap key must include the scopes required by the sections you use.

### Complete sandbox payment showcase

Open the **Checkout** section at `http://localhost:3000`. It runs a full synthetic journey without real money:

1. Enter an order, amount in minor units, account/device references, and a named test payment method.
2. The mock gateway returns approved, declined, or timeout.
3. FraudLens scores the same payment in shadow mode.
4. The merchant policy outcome remains separate from the FraudLens recommendation.
5. The payment timeline, transaction, assessment, alert, and audit event are persisted.

Use `test_approved` for the normal path, `test_declined` for a provider failure, and an amount above the configured risk threshold to demonstrate a payment that succeeds while FraudLens recommends review.

Score a synthetic transaction after bootstrapping a tenant key:

```bash
curl -X POST http://localhost:8000/v1/transactions/score \
  -H "Authorization: Bearer $FRAUDLENS_API_KEY" \
  -H "Idempotency-Key: demo-txn-10001" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_10001",
    "amount_minor": 2500000,
    "currency": "INR",
    "occurred_at": "2026-10-26T15:30:00Z",
    "account_ref": "acct_pseudo_501",
    "channel": "upi",
    "provider_status": "pending",
    "metadata": {"source": "merchant_simulator"}
  }'
```

The score is an explainable 0–100 prioritization index. FraudLens remains in shadow mode and does not authorize, decline, block, or move money.

The SDK has no implicit retries. Configure a strict timeout and always provide an idempotency key:

```python
from fraudlens_sdk import FraudLensClient, Transaction

with FraudLensClient("http://localhost:8000", api_key, timeout=2.0) as client:
    assessment = client.score_transaction(transaction, idempotency_key="merchant-event-10001")
```

Run the synthetic merchant example with `PYTHONPATH=sdk/python python3 examples/merchant_simulator/main.py`.

See [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md) for milestone gates and unresolved decisions.
