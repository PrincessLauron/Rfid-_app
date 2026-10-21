#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

if ! python -c "import fastapi,serial" >/dev/null 2>&1; then
  pip install -r requirements.txt
fi

echo "Starting standalone reader monitor at http://127.0.0.1:8010"
exec uvicorn reader_standalone.main:app --host 127.0.0.1 --port 8010 --reload
