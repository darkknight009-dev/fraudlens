# ADR 0004: No LLM in the Synchronous Scoring Path

- Status: Accepted
- Date: 2026-10-26

## Context
Synchronous risk scoring requires predictable latency, reproducibility, and traceable evidence. LLM output may be nondeterministic and can invent unsupported explanations.

## Decision
The scoring path uses deterministic rules and an explicit detector interface. Any future LLM is optional and may only summarize structured, already-computed evidence. It cannot set scores, invent signals, or trigger financial actions.

## Consequences
Positive: lower latency and clearer testing/governance.
Negative: natural-language investigation summaries are not a core MVP dependency.
