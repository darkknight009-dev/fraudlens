# Release Checklist

## Local/demo release
- [ ] Fresh clone setup tested.
- [ ] Docker Compose starts cleanly.
- [ ] Database migrations work from empty DB.
- [ ] Synthetic seed data clearly labeled.
- [ ] API and SDK contract tests pass.
- [ ] Tenant isolation tests pass.
- [ ] No secrets in git history/current tree.
- [ ] Lint, type checks, tests, and frontend build pass.
- [ ] API docs match implementation.
- [ ] Demo script works from a clean environment.
- [ ] Known limitations documented.

## Pilot release (not covered by MVP alone)
- [ ] Threat model and independent security review complete.
- [ ] Authentication, key rotation, tenant isolation verified.
- [ ] Retention and deletion tested.
- [ ] Backup/restore tested.
- [ ] Load and resilience tests complete.
- [ ] Observability and alerting active.
- [ ] Incident response and support ownership defined.
- [ ] Model governance review complete.
- [ ] Customer data-flow and legal review complete.
- [ ] Data processing terms and customer approval complete.
- [ ] SLOs, rollback, and change management documented.
