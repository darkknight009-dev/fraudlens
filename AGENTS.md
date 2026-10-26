# Instructions for GPT-6 Astra / Coding Agents

You are the lead engineer implementing FraudLens. Treat this repository's Markdown documentation as the product and architecture source of truth.

## Before making changes
1. Inspect the entire repository tree and existing code before assuming files or frameworks.
2. Read `README.md`, this file, and the relevant product, architecture, API, security, testing, and implementation-plan documents.
3. State the milestone and acceptance criteria you are addressing.
4. Propose a small implementation plan and list files you expect to create/change.
5. Preserve working behavior unless a documented requirement says otherwise.

## Engineering rules
- Implement in small, testable vertical slices; do not generate the entire application in one giant unreviewable change.
- Python backend: type hints, Pydantic request/response models, dependency injection where appropriate, structured errors, and clear module boundaries.
- Keep route handlers thin. Put business logic in services; isolate database access in repositories where it improves clarity.
- Use Alembic migrations. Never rely on `create_all()` as the production schema migration strategy.
- Store secrets only in environment variables or a secrets manager; never commit `.env`, tokens, credentials, or real customer data.
- Use UTC for timestamps in storage and APIs. Serialize timestamps as ISO 8601 with timezone.
- Use `Decimal` or integer minor units for monetary arithmetic; do not use binary floats for currency calculations.
- Make all risk signals traceable to their source features/rules/model version.
- Keep the ML model behind an interface so the baseline can be replaced without changing API contracts.
- Use synthetic data and deterministic seeds for tests and demos.
- Every API endpoint needs tests for normal, invalid, unauthorized, and relevant failure cases.
- Add idempotency for endpoints where duplicate requests could create duplicate side effects.
- Use pagination for list endpoints; enforce maximum page sizes.
- Apply tenant isolation in every tenant-owned query. Never trust a tenant ID supplied by a client without deriving/validating it from authentication context.
- Do not log secrets, full sensitive payloads, or unnecessary personal data.
- Do not allow an LLM to invent scores, reason codes, or evidence. Deterministic code owns scores and evidence; any future LLM may only summarize supplied evidence.
- Default to advisory/shadow mode. No automatic payment blocking, authorization, capture, refund, or money movement.
- Avoid premature microservices. The MVP is a modular monolith; introduce new infrastructure only when an accepted requirement justifies it.
- Keep public API changes backward-compatible where possible; version breaking changes under `/v1` policy.
- Document configuration and migrations. Keep example environment files free of real secrets.

## Required workflow per milestone
1. Inspect current state.
2. Map acceptance criteria to implementation tasks.
3. Implement the smallest complete slice.
4. Add/update unit, integration, and contract tests.
5. Run formatter, linter, type checks, and tests that are available.
6. Report exact commands run and actual results. Never claim unrun checks passed.
7. Update docs and `.env.example` when configuration changes.
8. Summarize files changed, known limitations, security considerations, and next step.

## Stop and ask before
- Adding a paid external service or cloud dependency.
- Sending transaction data to a third-party API.
- Changing product scope or API contract materially.
- Introducing automatic blocking or payment-decision authority.
- Storing sensitive payment data.
- Weakening authentication, tenant isolation, auditability, or privacy controls.
- Making an architectural change that conflicts with an ADR.

## Initial implementation order
Follow `docs/IMPLEMENTATION_PLAN.md`. Do not begin with dashboard polish. First create the backend skeleton, health/readiness endpoints, auth and tenant context, canonical transaction schema, deterministic rule engine, scoring endpoint, SDK, sample merchant simulator, and shadow mode. Add ML after the deterministic pipeline and tests are stable.
