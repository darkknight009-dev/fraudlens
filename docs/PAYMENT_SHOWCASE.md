# End-to-end payment showcase

## Local flow

```text
Checkout page
  ↓
Next.js server proxy
  ↓
POST /v1/sandbox/payments
  ↓
Mock payment gateway
  ↓
Canonical transaction + FraudLens rules
  ↓
Risk assessment and optional reviewed model
  ↓
Merchant policy result (kept separate)
  ↓
Payment timeline + alert + audit + webhook queue
```

The showcase is deliberately synthetic. It demonstrates the same boundaries used in a production integration without handling payment credentials or moving money.

## Scenarios

### Approved payment, low risk

- payment method: `test_approved`
- amount: `250000` minor units
- expected provider status: `approved`
- expected payment status: `succeeded`
- expected recommendation: `monitor`

### Approved payment, high risk in shadow mode

- payment method: `test_approved`
- amount: `2000000` minor units
- expected provider status: `approved`
- expected payment status: `succeeded`
- expected recommendation: `monitor` or `review` depending on active rules/model

This proves that a FraudLens recommendation does not silently block a merchant payment.

### Provider decline

- payment method: `test_declined`
- expected provider status: `declined`
- expected payment status: `failed`

The failure comes from the mock provider scenario, not from FraudLens.

## Training the baseline model

```bash
make train-model
```

This writes a local ignored artifact to `data/generated/fraudlens_isolation_forest.joblib` and a report to `docs/ml_training_report.json`. The training set is deterministic synthetic data with a temporal holdout. It is not production fraud performance.

To enable the reviewed artifact for local shadow inference, set:

```env
MODEL_ARTIFACT_PATH=data/generated/fraudlens_isolation_forest.joblib
```

If the API runs in Docker, the Compose file mounts `data/generated` read-only at `/app/data/generated`. Set `MODEL_ARTIFACT_PATH=/app/data/generated/fraudlens_isolation_forest.joblib` in the root `.env`, then restart the API. Assessments will report `detector_status.ml=complete` and include a traceable model signal when the detector prioritises a transaction. If the artifact is absent or invalid, the assessment reports ML as unavailable and rules remain traceable; the model never silently becomes a low-risk result.

## Production replacement points

| Showcase component | Production replacement |
|---|---|
| Next.js checkout form | Merchant checkout/application |
| Mock gateway | PSP/acquirer adapter owned by the merchant or payment platform |
| Named test payment method | PSP token/reference; never raw card credentials |
| Local API key bridge | OIDC/OAuth dashboard session and service-to-service credentials |
| Synthetic training rows | Approved, minimised, point-in-time production labels |
| Local worker commands | Durable queue worker/scheduler with monitoring |
| PostgreSQL Compose | Managed or customer-hosted PostgreSQL with backups |
