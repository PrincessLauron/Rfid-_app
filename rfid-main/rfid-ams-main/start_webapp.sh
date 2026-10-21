#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "[setup] Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

if ! python -c "import fastapi" >/dev/null 2>&1; then
  echo "[setup] Installing dependencies..."
  pip install -r requirements.txt
fi

echo "[db] Running migrations..."
alembic upgrade head

echo "[db] Seeding defaults..."
python -m backend.app.seed

echo "[web] Starting app at http://127.0.0.1:8000"
exec uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
