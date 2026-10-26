# ADR 0001: Start with a Modular Monolith

- Status: Accepted
- Date: 2026-10-26

## Context
The MVP needs multiple logical capabilities but limited development and operational complexity. Premature microservices would increase deployment, security, and observability burden.

## Decision
Build a modular monolith with clear boundaries for API, integration adapters, rules, detectors, scoring, cases, audit, and persistence. Use separate workers only when async processing becomes a justified milestone.

## Consequences
Positive: simpler local development, testing, transactions, and deployment.
Negative: module boundaries require discipline; scale-out is initially at application level.
Revisit when measured throughput, independent release cadence, or failure isolation justifies separation.
