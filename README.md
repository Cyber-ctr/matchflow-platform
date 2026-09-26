# MatchFlow — Production Web/PWA

MatchFlow is a mobile-first talent marketplace for Cameroon-focused SME hiring, junior freelance work and structured apprenticeships. The application is designed so the same backend can later support native mobile clients.

## What is included

- Flask application factory and modular blueprints
- PostgreSQL-ready SQLAlchemy data model
- SQLite fallback for local development
- Secure authentication and role-based access: talent, employer, admin
- Talent profiles, skills, trust score and verification status
- Employer business profiles and verification status
- Opportunity creation, search, filtering and management
- Skill-based match scoring and recommendations
- Applications and employer pipeline statuses
- Saved opportunities
- In-platform messaging and notifications
- Apprenticeship records and acceptance/management workflow
- Skill assessments and scoring
- Reviews and feedback records
- Payment data model + provider-neutral payment service
- Audit-ready schema for operational logging
- Global CSRF protection
- Rate limiting
- Secure password hashing using Werkzeug scrypt
- Security headers and optional proxy/HTTPS configuration
- PWA manifest, service worker, icons and mobile navigation
- Docker and PostgreSQL Compose setup
- Render deployment definition
- Demo seeding commands
- Pytest smoke tests

## Important production note

This repository is a production-oriented foundation, but it is not a claim that every external integration is live. SMTP password-reset delivery and Mobile Money payment processing require your own provider credentials and business onboarding. The payment service intentionally creates pending records instead of pretending to execute a live transaction without credentials.

## 1. Local setup — Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
flask --app wsgi:app bootstrap-db
flask --app wsgi:app seed-assessments
flask --app wsgi:app seed-demo
python run.py
```

Open `http://127.0.0.1:5000`.

Demo accounts created by `seed-demo`:

- Talent: `demo.talent@matchflow.local` / `DemoTalent@123`
- Employer: `demo.sme@matchflow.local` / `DemoEmployer@123`

Do not use demo credentials in a production environment.

## 2. Local setup — Linux/Kali

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
flask --app wsgi:app bootstrap-db
flask --app wsgi:app seed-assessments
flask --app wsgi:app seed-demo
python run.py
```

## 3. Admin account

After installing dependencies:

```bash
flask --app wsgi:app create-admin
```

Then use the email/password you supplied at `/auth/login`.

## 4. PostgreSQL

Set `DATABASE_URL` in `.env` to a PostgreSQL connection string, for example:

```text
postgresql+psycopg://matchflow:strong-password@localhost:5432/matchflow
```

Then run:

```bash
flask --app wsgi:app bootstrap-db
flask --app wsgi:app seed-assessments
```

For schema evolution, use Flask-Migrate:

```bash
flask --app wsgi:app db init
flask --app wsgi:app db migrate -m "initial schema"
flask --app wsgi:app db upgrade
```

Once real migration history exists, use `db upgrade` during deployment instead of relying on `bootstrap-db` for schema changes.

## 5. Docker

```bash
docker compose up --build
```

The web service is exposed at `http://localhost:8000`.

## 6. Render

The included `render.yaml` provisions a web service and PostgreSQL database. For a new deployment:

1. Push this repository to GitHub.
2. Create a Render Blueprint from the repository.
3. Review the generated database connection.
4. Set `TRUSTED_HOSTS` to your real domain once known.
5. Set `SESSION_COOKIE_SECURE=1`.
6. Configure SMTP before relying on password-reset email.
7. Configure Redis for rate limiting when you have multiple instances.

For production, prefer a managed Redis/Valkey service rather than the in-memory limiter store.

## 7. Directory structure

```text
MatchFlow_Production/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── cli.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes.py
│   ├── auth/
│   ├── main/
│   ├── talent/
│   ├── employer/
│   ├── admin/
│   ├── api/
│   ├── services/
│   ├── utils/
│   ├── templates/
│   └── static/
├── tests/
├── docs/
├── scripts/
├── migrations/
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── Procfile
├── requirements.txt
└── wsgi.py
```

## 8. Recommended next engineering steps

1. Connect your chosen Mobile Money providers through `app/services/payments.py` and add webhook verification.
2. Add email verification before enabling higher-trust actions.
3. Add identity/business verification workflows that match your compliance requirements.
4. Put rate limiting in Redis/Valkey for multi-instance deployments.
5. Add centralized structured logging and an error-monitoring service.
6. Add object storage (S3-compatible) for CVs/avatars instead of local disk.
7. Add automated backups and restore tests for PostgreSQL.
8. Add stronger anti-fraud and moderation tooling as user volume grows.
9. Add employer subscriptions and invoices after validating willingness to pay.
10. Build the Android client against `/api/v1` only after the web marketplace has validated product-market fit.
