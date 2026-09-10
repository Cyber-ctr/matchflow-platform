# MatchFlow Production Build Status

## Verified in this environment

- Python source files pass AST parsing.
- Python bytecode compilation passes with `compileall`.
- Jinja templates parse successfully.
- `render.yaml` and `docker-compose.yml` parse as YAML.
- Final PWA app icon/favicon assets are present.

## Not executable in this environment

The runtime dependency installation could not be completed because this environment has no external package-index/network access. Therefore a live Flask/PostgreSQL integration test was not possible here. Install `requirements.txt` in your development/deployment environment and run `pytest -q` before public launch.

The external services below also require your own credentials/onboarding:

- PostgreSQL production instance
- SMTP email provider
- Redis/Valkey for distributed rate limits
- Mobile Money provider credentials and webhook contracts
- Object storage for production CV/document files
