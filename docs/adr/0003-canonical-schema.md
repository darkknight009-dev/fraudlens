# ADR 0003: Canonical Transaction Schema

- Status: Accepted
- Date: 2026-10-26

## Context
Integrating systems use different field names and payload formats. Detector code should not depend on provider-specific schemas.

## Decision
Normalize supported input through validated adapters into a canonical transaction schema. Use integer minor currency units, ISO currency codes, UTC timestamps, and pseudonymous references. Unknown fields are not automatically trusted as model features.

## Consequences
Positive: stable detector interfaces, contract tests, and easier SDK integration.
Negative: adapters and mapping configuration need versioning and validation.
