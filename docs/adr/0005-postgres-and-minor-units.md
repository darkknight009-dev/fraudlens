# ADR 0005: PostgreSQL and Integer Minor Currency Units

- Status: Accepted
- Date: 2026-10-26

## Context
FraudLens needs relational integrity for tenants, transactions, assessments, cases, and audit records. Currency arithmetic must avoid floating-point rounding errors.

## Decision
Use PostgreSQL for MVP persistence and store amounts as integer minor units with ISO currency codes. Use `TIMESTAMPTZ` in UTC and Alembic migrations.

## Consequences
Positive: strong constraints, transactions, JSONB for controlled metadata, and reliable money arithmetic.
Negative: currencies with unusual minor-unit conventions require currency metadata rather than assuming all currencies use two decimal places.
