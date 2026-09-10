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

## Database initialization

For the first deployment, the included Render start command bootstraps the schema and starter assessments. Once Flask-Migrate history is established, change the start process to run `flask --app wsgi:app db upgrade` before Gunicorn.

## Scaling

When scaling beyond one web instance:

- Use Redis/Valkey for the rate limiter.
- Use external object storage for uploads.
- Ensure all application state is in PostgreSQL or another shared service.
- Keep Gunicorn workers stateless.
