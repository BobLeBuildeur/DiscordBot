#!/usr/bin/env bash
# Create .venv in this service, install editable + dev deps, seed .env if missing.
# Run from services/auth-service: ./scripts/bootstrap.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  echo "Created .venv"
fi

# shellcheck source=/dev/null
source .venv/bin/activate

python -m pip install -U pip
pip install -e ".[dev]"

if [[ ! -f .env ]] && [[ -f .env.example ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — set JWT_SIGNING_SECRET before running the API."
fi

echo "Bootstrap complete. Activate the venv with: source \"${SCRIPT_DIR}/activate-venv.sh\""
