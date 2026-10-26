# Local PostgreSQL Backup and Restore

The MVP uses PostgreSQL in Docker Compose. Before any pilot, run and verify a backup/restore exercise with synthetic data:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup.sql
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < backup.sql
```

Hosted deployments must use managed backup policy or an approved equivalent, define encryption and retention, and test restoration into an isolated database. Do not place credentials or customer data in this document or source control.
