# Render Deployment Guide

## Prerequisites

- GitHub repository containing this project
- Render account
- Production domain when ready
- PostgreSQL database from Render

## Blueprint

The repository includes `render.yaml`. Create a Blueprint from the GitHub repository and review the generated resources.

## Environment variables

Set at minimum:

```text
SECRET_KEY=<generated-long-random-secret>
DATABASE_URL=<Render PostgreSQL URL>
FLASK_ENV=production
SESSION_COOKIE_SECURE=1
TRUST_PROXY=1
TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com
```

For password-reset email:

```text
MAIL_SERVER=...
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_DEFAULT_SENDER=...
```

For rate limiting across multiple instances, configure a shared Redis/Valkey service URL as `RATELIMIT_STORAGE_URI` (or `REDIS_URL`). Use `rediss://` when the service requires TLS. The application defaults to in-memory counters for local single-instance development; in-memory counters are not shared across instances.

For error monitoring, set `SENTRY_DSN`. For private S3-compatible uploads, set `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_REGION`, and optionally `OBJECT_STORAGE_ENDPOINT_URL` and `OBJECT_STORAGE_PREFIX`; provide credentials using Render secret environment variables. Copy any existing local uploads to the matching bucket prefix before switching storage.

Existing deployments should run `flask --app wsgi:app bootstrap-db` to add new nullable moderation review-note storage. Admins must record the evidence checked and rationale for each report status update; the decision and note are retained in the audit log.

## Database initialization

For the first deployment, the included Render start command bootstraps the schema and starter assessments. `bootstrap-db` also creates the moderation table and adds the nullable talent avatar key column on existing databases. Establish migration history for future schema changes; generate and review a migration before switching the start process to `flask --app wsgi:app db upgrade`.

## Scaling

When scaling beyond one web instance:

- Set `RATELIMIT_STORAGE_URI` (or `REDIS_URL`) to a shared Redis/Valkey service for the rate limiter. Docker Compose runs a local Valkey service automatically.
- Use a private S3-compatible bucket for uploads.
- Ensure all application state is in PostgreSQL or another shared service.
- Keep Gunicorn workers stateless.
- Render does not run the Compose backup sidecar. Enable managed PostgreSQL backups and use a trusted scheduled runner to create off-site archives and periodically run `scripts/postgres-backup.sh restore-test <archive>`.
