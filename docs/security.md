# MatchFlow Security Checklist

## Implemented in the codebase

- CSRF protection for state-changing browser requests
- Secure password hashing via Werkzeug scrypt
- HTTP-only, SameSite session cookies
- Optional secure cookies for HTTPS deployments
- Rate limits for authentication and account creation
- Safe internal redirect validation after login
- Security headers: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy and Permissions-Policy
- Server-side role checks for talent/employer/admin routes
- SQLAlchemy parameterization instead of handwritten SQL
- Jinja autoescaping for user-generated text
- Maximum request/upload size configuration
- Password reset links are time-limited and signed

## Required before public launch

- Replace the default secret and keep it outside the repository.
- Use HTTPS and `SESSION_COOKIE_SECURE=1`.
- Set `TRUSTED_HOSTS` for the real domain.
- Use PostgreSQL with a least-privilege application user.
- Configure Redis/Valkey for rate-limit state when horizontally scaling.
- Add account email verification and recovery controls.
- Add abuse reporting, moderation and suspicious-login monitoring.
- Add cloud object storage for uploaded documents; never store large user files on ephemeral Render/local disk.
- Add automated database backups and verify restore procedures.
- Restrict admin accounts and enable stronger admin authentication before high-value payment actions.
- Integrate a payment provider only after validating webhook signatures and idempotency.
