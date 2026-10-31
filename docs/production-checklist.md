# Production Launch Checklist

## Application

- [ ] Set a unique high-entropy `SECRET_KEY`.
- [ ] Configure production `DATABASE_URL`.
- [ ] Create an admin account with a unique password.
- [ ] Establish Flask-Migrate migration history and deploy with `db upgrade`.
- [ ] Run `flask --app wsgi:app bootstrap-db` on existing installations to create the moderation table and add the talent avatar key column before switching deployment startup away from that command.
- [ ] Configure `TRUSTED_HOSTS` to the actual domain.
- [ ] Set `SESSION_COOKIE_SECURE=1` and `TRUST_PROXY=1` behind HTTPS reverse proxy.

## Identity and trust

- [ ] Configure SMTP, verify account links expire, and test that unverified accounts cannot apply, message, post jobs, use billing, or request verification.
- [ ] Test password reset delivery and expiry.
- [ ] Align the generic talent/business review flow with applicable compliance rules before requesting or storing sensitive evidence; the current flow only records profile context and reviewer rationale, with no document uploads.
- [ ] Assign a moderation owner and response targets for reports.
- [ ] Review open reports daily: check the relevant profile/listing and supporting evidence, request clarification where needed, and record the evidence checked and rationale in the admin review note before resolving or dismissing a report.
- [ ] Keep reports open or under review while investigating; escalate credible immediate safety risks through the documented incident process.
- [ ] Base account/listing actions on corroborated policy violations and proportional decisions, not report counts alone.
- [ ] Never automatically lower trust scores or disable accounts based on report volume; use reports as human-review signals only.

## Marketplace

- [ ] Recruit the first pilot SMEs manually.
- [ ] Seed or onboard real skill taxonomies relevant to the pilot.
- [ ] Validate match score quality against employer decisions.
- [ ] Establish apprenticeship templates, dispute handling and completion criteria.

## Payments

- [ ] Register the business with the selected payment providers.
- [ ] Put provider credentials in a secret manager/environment variables.
- [ ] Implement provider callbacks/webhooks.
- [ ] Verify callback signatures and idempotency.
- [ ] Reconcile provider status against the `payments` table.
- [ ] Test refunds/failed payments before charging real users.

## Operations

- [ ] Set `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_REGION`, and (if needed) `OBJECT_STORAGE_ENDPOINT_URL`; provide credentials through the runtime's secret store or standard AWS credential chain.
- [ ] Keep the object bucket private and use least-privilege access; verify CV downloads require the existing talent/employer authorization checks.
- [ ] Before enabling object storage for an existing installation, copy `instance/uploads/` into the configured bucket prefix so existing CV keys continue to resolve.
- [ ] Set `SENTRY_DSN` to enable Flask error monitoring. Keep `send_default_pii` disabled and never put tokens or upload contents into log messages.
- [ ] Ship JSON application logs to a centralized log service and alert on elevated 5xx rates and error-monitoring events.
- [ ] For Docker Compose, verify the `db-backup` service creates daily archives in the `matchflow_backups` volume and performs a restore test weekly.
- [ ] Copy backups off the application host to encrypted, access-controlled storage; configure retention and alert on failed jobs.
- [ ] For non-Compose PostgreSQL, schedule `scripts/postgres-backup.sh backup` and periodically run `scripts/postgres-backup.sh restore-test <archive>` with PostgreSQL client tools installed and a role allowed to create/drop temporary databases.
- [ ] Record restore-test results and verify recovery-point and recovery-time objectives.
- [ ] Set `RATELIMIT_STORAGE_URI` to a shared Redis/Valkey service before running multiple web instances.
- [ ] Monitor response time, failed requests, signups, applications, matches and paid conversions.
