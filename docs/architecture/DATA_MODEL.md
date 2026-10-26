# Data Model

Use PostgreSQL and SQLAlchemy. Use Alembic for all schema changes. All tenant-owned tables include `tenant_id` and all queries must enforce tenant scope.

## Entities
### Tenant
- `id` UUID primary key
- `name`
- `status` (`active`, `suspended`)
- `created_at`, `updated_at`

### APIKey
- `id` UUID
- `tenant_id`
- `key_prefix` (non-secret lookup prefix)
- `key_hash` (secure hash)
- `scopes` (normalized list or related table)
- `expires_at`, `revoked_at`, `last_used_at`
- `created_by`, `created_at`
Never store plaintext key after initial display.

### Transaction
- `id` UUID internal primary key
- `tenant_id`
- `external_transaction_id`
- `amount_minor` BIGINT
- `currency` CHAR(3)
- `occurred_at` TIMESTAMPTZ
- `account_ref_hash` or pseudonymous reference, based on retention needs
- `device_ref_hash` nullable
- `merchant_ref` nullable
- `channel`
- `provider_status` nullable
- `safe_metadata` JSONB allowlisted
- `created_at`
Unique constraint: `(tenant_id, external_transaction_id)` unless domain requirements explicitly allow multiple events per transaction, in which case model event identity separately.

### Assessment
- `id` UUID
- `tenant_id`
- `transaction_id` FK
- `risk_score` SMALLINT constrained 0..100
- `risk_level`
- `mode` (`shadow`, `advisory`)
- `assessment_status` (`complete`, `partial`, `unavailable`)
- `rule_set_version`
- `model_version` nullable
- `feature_snapshot` JSONB minimized and versioned
- `detector_status` JSONB
- `request_id`
- `created_at`

### RiskSignal
- `id` UUID
- `tenant_id`
- `assessment_id` FK
- `reason_code`
- `source` (`rule`, `model`, `feature`)
- `severity`
- `message_template_key`
- `evidence` JSONB allowlisted
- `contribution` nullable
- `created_at`

### Alert / Case
- `id` UUID
- `tenant_id`
- `assessment_id` FK
- `status` (`open`, `in_review`, `resolved`, `false_positive`, `escalated`)
- `priority`
- `assigned_to` nullable
- `disposition` nullable
- `created_at`, `updated_at`, `closed_at`
Deduplication should be based on a documented alert key, such as tenant + transaction + reason-group + configurable time window.

### CaseNote
- `id` UUID
- `tenant_id`
- `case_id` FK
- `author_id` nullable for service-generated note
- `body` bounded text
- `created_at`

### RuleSetVersion
- `id` UUID
- `tenant_id`
- `version`
- `configuration` JSONB validated against a strict schema
- `created_by`
- `created_at`
- `is_active`
Do not overwrite historical versions.

### AuditEvent
- `id` UUID
- `tenant_id` nullable only for platform-level events
- `actor_type`, `actor_id`
- `action`
- `target_type`, `target_id`
- `request_id`
- `details_redacted` JSONB
- `created_at`
Append-oriented. Avoid storing raw request bodies.

### IdempotencyRecord
- `id` UUID
- `tenant_id`
- `endpoint`
- `key_hash`
- `request_fingerprint`
- `response_status`
- `response_body` (only the minimal safe response)
- `expires_at`, `created_at`
Unique: `(tenant_id, endpoint, key_hash)`.

### WebhookEndpoint / WebhookDelivery (later)
Store endpoint metadata, secret reference (not plaintext), event subscription, retry state, response status, and timestamps. Do not expose signing secrets.

## Data rules
- Use UTC `TIMESTAMPTZ`.
- Monetary values use integer minor units.
- Apply foreign keys and indexes for tenant/date/status lookup.
- Index common queries: `(tenant_id, created_at)`, `(tenant_id, risk_level, created_at)`, `(tenant_id, status, created_at)`, and external transaction ID.
- Use soft deletion only where justified; document retention and deletion semantics.
- Use transaction boundaries for assessment + signals + case creation.
- Tenant isolation tests are mandatory for every repository and endpoint.
