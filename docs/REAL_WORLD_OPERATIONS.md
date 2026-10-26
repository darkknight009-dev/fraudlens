# How FraudLens works in the real world

FraudLens is an intelligence and investigation layer placed beside an existing payment or transaction system. It does not become the payment processor and it does not own the final authorisation decision.

## 1. Transaction path

```text
Customer action
    ↓
Merchant / fintech transaction system
    ├── keeps its existing payment policy and outcome
    └── sends a canonical event to FraudLens
             ↓
       validation + tenant resolution
             ↓
       deterministic rules + optional reviewed detector
             ↓
       bounded 0–100 prioritisation assessment
             ↓
       alert / webhook / audit side effects
```

For a synchronous integration, the merchant calls `POST /v1/transactions/score` with a tenant-scoped API key and an idempotency key. FraudLens validates the payload, persists the transaction and assessment, evaluates the active rule set, and returns an explainable assessment. The merchant's existing policy engine decides whether the transaction is approved, reviewed, or declined.

For an asynchronous integration, the merchant sends `POST /v1/events`. FraudLens stores the event in the durable inbox and returns `202 Accepted`. A bounded worker later runs the same scoring service. Duplicate tenant/event IDs are ignored safely.

## 2. What analysts see

The Next.js console is a live operations surface, not a demo dashboard. It reads tenant-scoped alerts through server-side proxy routes, keeping the integration key out of the browser. Analysts can:

- triage the alert queue by status and search fields;
- open the linked case and inspect score, ownership, assessment, and timestamps;
- move a case through validated statuses;
- add bounded case notes;
- use audit records to reconstruct security-sensitive actions.

The console maps actions to API scopes: alert queue and case updates use `cases:read` / `cases:write`; transaction lookup and scoring use `transactions:read` / `transactions:score`; rule publishing uses `config:read` / `config:write`; audit trail uses `audit:read`; webhook management uses `config:read` / `config:write`.

When there are no alerts, the UI shows an empty operational state. It does not invent transactions, scores, charts, or activity.

## 3. Where webhooks fit

Alert creation only enqueues a durable delivery record. A separate worker signs the payload with HMAC-SHA256, sends it to a configured HTTPS endpoint, retries with bounded backoff, and moves exhausted deliveries to a dead-letter state. A webhook outage cannot change the synchronous scoring response.

## 4. Tenant and data boundaries

Every request resolves its tenant from authentication. Tenant IDs are never accepted from the browser as authority. Account and device references are pseudonymised before persistence, and the API rejects payment credentials such as PAN, CVV, PIN, OTP, and passwords.

The browser console uses `FRAUDLENS_DASHBOARD_API_KEY` only as a local/internal bridge for this MVP. A customer deployment should replace that bridge with OIDC/OAuth, short-lived sessions, role-based access, CSRF protection, and an audit-aware identity provider before exposing the console to analysts.

## 5. A realistic rollout

1. Start in shadow mode beside the merchant's existing decision engine.
2. Measure score distribution, alert volume, latency, false positives, analyst handling time, and webhook delivery health.
3. Tune versioned rules with `config:read` / `config:write`, recording each change in the audit trail.
4. Introduce reviewed model artifacts only after point-in-time evaluation and governance approval.
5. Keep FraudLens advisory until the merchant has independently validated policy, controls, monitoring, and incident procedures.

## Design references used

The console direction follows queue-first investigation patterns and operational density seen in Checkmarble's Case Manager documentation, SAP Fiori enterprise workflow principles, and fraud operations case studies from Synctera and Worxwide. The implementation deliberately avoids decorative glassmorphism, fake analytics, unsupported maps, and fabricated data.
