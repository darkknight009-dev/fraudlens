# Customer-hosted deployment profile

FraudLens is currently a modular monolith packaged as a container. A customer-hosted deployment must use a reviewed release artifact and customer-managed PostgreSQL/secrets.

## Required components

- API container running as a non-root user.
- PostgreSQL 16 or a compatible supported version.
- Customer-managed secret injection for `DATABASE_URL`, `API_KEY_HASH_PEPPER`, and, when webhooks are enabled, `WEBHOOK_ENCRYPTION_KEY`.
- TLS termination outside or in front of the API.
- Egress allowlist limited to approved webhook destinations and operational dependencies.
- Persistent PostgreSQL storage with backups and a tested restore process.

## Release procedure

1. Pull the signed/versioned image and verify its digest through the approved release channel.
2. Validate configuration with `python scripts/validate_config.py` in the deployment environment.
3. Back up PostgreSQL.
4. Run `python -m alembic upgrade head` as an explicit migration step using migration credentials.
5. Deploy the API with runtime credentials that cannot alter schema.
6. Check `/health/live` and `/health/ready`.
7. Run a synthetic scoring smoke test and verify shadow mode.
8. Record image digest, migration revision, configuration revision, and operator in the change log.

## Network and data boundaries

The API accepts only canonical transaction data and must not receive PAN, CVV, PIN, OTP, passwords, bank-login credentials, or authentication secrets. Webhook destinations must be HTTPS and are validated against private/local literal addresses. DNS/IP revalidation and a customer egress proxy are required for higher-assurance deployments.

## Rollback

Rollback uses the previous application image only when its migration compatibility is documented. Database downgrade is not an automatic rollback; use a reviewed forward migration or restore into an isolated database after backup verification.
