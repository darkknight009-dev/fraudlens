# ADR 0002: Advisory and Shadow Mode by Default

- Status: Accepted
- Date: 2026-10-26

## Context
Fraud assessments can create customer harm if incorrect. The MVP lacks production validation and must not control money movement.

## Decision
FraudLens computes and returns risk intelligence only. Shadow mode is the default. The integrating company's existing policy engine retains all payment decision authority. No automatic block/decline feature in MVP.

## Consequences
Positive: safer integration and offline evaluation; easy comparison with existing decisions.
Negative: the prototype does not demonstrate autonomous blocking; customer-specific decision policy remains external.
Revisit only after formal product, legal, security, model governance, and customer approvals.
