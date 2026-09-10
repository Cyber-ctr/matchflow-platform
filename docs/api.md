# MatchFlow API v1

The API is intentionally small in the first web release so native mobile clients can be added after product validation.

## Health

`GET /api/v1/health`

Returns application and database health.

## Public opportunities

`GET /api/v1/jobs?q=&category=`

Returns up to 50 published opportunities.

## Current session

`GET /api/v1/me`

Requires a logged-in browser session and returns the current user identity/role.

## Future mobile authentication

Before shipping Android/iOS, add a token-based authentication flow (short-lived access token + refresh token rotation), mobile-specific rate limits, and revocation support. Do not reuse browser session cookies as the final mobile authentication mechanism.
