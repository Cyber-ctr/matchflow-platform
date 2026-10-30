# MatchFlow Architecture

## High-level

```text
                       +----------------------+
                       |  MatchFlow Web/PWA   |
                       |  HTML/CSS/JS         |
                       +----------+-----------+
                                  |
                                  v
                       +----------------------+
                       | Flask Application     |
                       | Blueprints + Services |
                       +----------+-----------+
                                  |
               +------------------+------------------+
               |                  |                  |
               v                  v                  v
        +-------------+    +-------------+    +-------------+
        | Auth / RBAC |    | Marketplace |    | Operations  |
        | sessions    |    | jobs/apps   |    | admin/audit |
        +-------------+    +-------------+    +-------------+
                                  |
                                  v
                       +----------------------+
                       | SQLAlchemy           |
                       | PostgreSQL / SQLite  |
                       +----------------------+

       +-------------------+        +--------------------------+
       | Private object    |        | JSON logs + optional      |
       | storage for files |        | Sentry error monitoring   |
       +-------------------+        +--------------------------+

                         Future mobile clients
                               /api/v1
                              /     \
                         Android    iOS
```

## Design principles

- The backend owns all business rules and authorization.
- Templates are mobile-first and do not depend on a large JavaScript framework.
- The API namespace is versioned so native apps can be introduced later without rewriting core services.
- Services contain matching, notification and payment logic so those components can evolve independently.
- `app/services/storage.py` keeps upload handling provider-neutral: local storage is used for development, while an S3-compatible bucket is selected when configured.
- Application logs are JSON with request IDs; configure `SENTRY_DSN` to forward unhandled errors to Sentry without sending default PII.
- User and opportunity reports enter an admin review queue. Moderation decisions are audited and are not automated based on report counts.
- PostgreSQL is the production target; SQLite is only a convenience for local development/testing.
