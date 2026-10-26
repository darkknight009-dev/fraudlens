# FraudLens MVP Demo Plan

## Objective
Demonstrate an integration-first fraud intelligence layer working with a simulated merchant, with no real payment rails or real customer data.

## Demo setup
- Docker Compose services running.
- Demo tenant and synthetic API key created through a documented seed command.
- Synthetic dataset generated using a fixed seed.
- Sample merchant simulator configured with FraudLens base URL.
- Dashboard visibly displays `DEMO / SYNTHETIC DATA` and `SHADOW MODE`.

## Demo story
1. Show the simulated merchant's existing transaction flow.
2. Send a normal transaction through the SDK.
3. Show a low-risk or low-signal assessment; explain that low risk is not a guarantee of safety.
4. Send a synthetic burst of transactions from one account/device.
5. Show velocity/amount signals and the assessment.
6. Show the alert/case created under configured rules.
7. Open the case, inspect reason codes and evidence, add an analyst note, and set a disposition.
8. Show audit history.
9. Stop or misconfigure the ML detector and demonstrate an explicit partial/unavailable state rather than a silently safe score.
10. Show that the merchant simulator's original payment outcome remains unchanged in shadow mode.
11. Show API latency and error metrics if implemented.

## Evidence to capture
- OpenAPI docs.
- SDK code snippet.
- Request and response examples with synthetic IDs.
- Test report.
- ML evaluation report and limitations.
- Latency report with hardware/config/load stated.
- Architecture diagram.
- Tenant-isolation test results.

## Claims to avoid
- “Detects all fraud.”
- “Production-ready for any fintech.”
- “87 means 87% probability of fraud.”
- “Used by Paytm/Razorpay” unless formally true and approved.
- “Compliant/certified” without an applicable independent assessment.
- Any results derived from synthetic data described as real-world business outcomes.
