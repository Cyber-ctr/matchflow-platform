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
- PostgreSQL is the production target; SQLite is only a convenience for local development/testing.
