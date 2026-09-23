#!/usr/bin/env bash
# ANVEṢHA AI — single command to run all automated tests.
set -e
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "No .venv found — create one with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "== Backend tests (pytest) =="
.venv/bin/python -m pytest tests/ -v

echo
echo "== Frontend build/type-check =="
(cd frontend && npm run build)

echo
echo "All checks passed."
