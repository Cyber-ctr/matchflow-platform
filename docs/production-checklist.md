# Production Launch Checklist

## Application

- [ ] Set a unique high-entropy `SECRET_KEY`.
- [ ] Configure production `DATABASE_URL`.
- [ ] Create an admin account with a unique password.
- [ ] Establish Flask-Migrate migration history and deploy with `db upgrade`.
- [ ] Configure `TRUSTED_HOSTS` to the actual domain.
- [ ] Set `SESSION_COOKIE_SECURE=1` and `TRUST_PROXY=1` behind HTTPS reverse proxy.

## Identity and trust

- [ ] Configure SMTP and test email verification.
- [ ] Test password reset delivery and expiry.
- [ ] Define talent/business verification procedures.
- [ ] Define abuse, fraud and moderation response process.

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

- [ ] Use PostgreSQL backups and test a restore.
- [ ] Move uploads to S3-compatible storage.
- [ ] Move rate limiting to Redis/Valkey for multiple web instances.
- [ ] Configure central logs/error monitoring.
- [ ] Monitor response time, failed requests, signups, applications, matches and paid conversions.
