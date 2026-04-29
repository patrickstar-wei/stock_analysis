#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/environment.yml"
ENV_NAME="${ENV_NAME:-financial_report_service}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD_FLAG="${RELOAD:-true}"

if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda not found. Install Anaconda/Miniconda first." >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] environment file not found: $ENV_FILE" >&2
  exit 1
fi

# Initialize conda in current shell.
eval "$(conda shell.bash hook)"

if ! conda env list | awk '{print $1}' | grep -Fxq "$ENV_NAME"; then
  echo "[INFO] Creating conda env: $ENV_NAME"
  conda env create -f "$ENV_FILE" -n "$ENV_NAME"
else
  echo "[INFO] Conda env already exists: $ENV_NAME"
fi

echo "[INFO] Activating env: $ENV_NAME"
conda activate "$ENV_NAME"

cd "$ROOT_DIR"

# Fail fast if port is already in use.
if command -v lsof >/dev/null 2>&1; then
  if lsof -Pi :"$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[ERROR] Port $PORT is already in use." >&2
    echo "[HINT] Run: lsof -i :$PORT" >&2
    echo "[HINT] Or change port: PORT=9000 ./start_with_conda.sh" >&2
    exit 1
  fi
fi

echo "[INFO] Open in browser:"
echo "       http://127.0.0.1:$PORT/docs"
echo "       http://127.0.0.1:$PORT/api/v1/healthz"

if [[ "$RELOAD_FLAG" == "true" ]]; then
  echo "[INFO] Starting service with reload on http://$HOST:$PORT"
  exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
  echo "[INFO] Starting service on http://$HOST:$PORT"
  exec uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
