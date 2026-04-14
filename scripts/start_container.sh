#!/usr/bin/env bash
set -euo pipefail

FRONTEND_DIR="${FRONTEND_DIR:-/app/frontend_dist}"
# Azure Web App commonly exposes the assigned container port via WEBSITES_PORT.
PORT="${WEBSITES_PORT:-${PORT:-8000}}"

mkdir -p "${FRONTEND_DIR}"

export FRONTEND_DIR
python - <<'PY'
import json
import os
from pathlib import Path

frontend_dir = Path(os.environ["FRONTEND_DIR"])
frontend_dir.mkdir(parents=True, exist_ok=True)

env_payload = {
    "ENTRA_CLIENT_ID": os.getenv("ENTRA_CLIENT_ID", ""),
    "ENTRA_AUTHORITY": os.getenv("ENTRA_AUTHORITY", ""),
    "ENTRA_REDIRECT_URI": os.getenv("ENTRA_REDIRECT_URI", ""),
    "API_BASE_URL": os.getenv("API_BASE_URL", "/api"),
}

(frontend_dir / "env-config.js").write_text(
    "window.__env = " + json.dumps(env_payload, ensure_ascii=True, indent=2) + ";\n",
    encoding="utf-8",
)
PY

exec uvicorn src.main:app --app-dir /app/backend --host 0.0.0.0 --port "${PORT}"
