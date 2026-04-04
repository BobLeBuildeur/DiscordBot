# Monorepo scripts

| Path | Purpose |
|------|---------|
| [`auth-service/bootstrap.sh`](auth-service/bootstrap.sh) | Create `services/auth-service/.venv`, install editable package + dev deps, seed `.env` if missing |
| [`auth-service/activate-venv.sh`](auth-service/activate-venv.sh) | `source` to activate that venv (run from repo root) |

Same behavior is available under the service: `services/auth-service/scripts/bootstrap.sh` and `activate-venv.sh` (paths resolve to that service directory).
