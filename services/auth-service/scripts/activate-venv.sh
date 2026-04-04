#!/usr/bin/env bash
# Activate the auth-service Python venv in your current shell.
# Usage (from monorepo root):
#   source services/auth-service/scripts/activate-venv.sh
# Or from services/auth-service:
#   source ./scripts/activate-venv.sh
#
# Do not run with ./activate-venv.sh — activation only applies after `source`.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PY="${ROOT}/.venv/bin/activate"

if [[ ! -f "$VENV_PY" ]]; then
  echo "No venv at ${ROOT}/.venv — run ./scripts/bootstrap.sh from services/auth-service first (or scripts/auth-service/bootstrap.sh from the monorepo root)." >&2
  return 2 2>/dev/null || exit 2
fi

# shellcheck source=/dev/null
source "$VENV_PY"
