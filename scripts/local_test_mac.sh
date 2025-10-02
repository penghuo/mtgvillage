#!/usr/bin/env bash
# Run backend smoke test and serve the frontend for local development on macOS/Linux.
set -euo pipefail

PORT="${1:-8000}"
BACKEND_PORT="${2:-3000}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required (3.9 or newer)." >&2
    exit 1
fi

echo "Installing backend dependencies..."
python3 -m pip install -r requirements.txt

echo "Running backend smoke test..."
python3 - <<'PY'
import sys
from pathlib import Path

repo_root = Path.cwd()
scripts_dir = repo_root / "scripts"
sys.path.insert(0, str(scripts_dir))

from mtg_price_checker import MTGPriceChecker

config_path = scripts_dir / "config.json"
checker = MTGPriceChecker(config_file=str(config_path))
stores = ", ".join(checker.stores.keys()) or "none"
print(f"Configured stores: {stores}")
PY

echo "Starting local API server at http://127.0.0.1:${BACKEND_PORT}"
python3 "$SCRIPT_DIR/local_backend_server.py" --port "$BACKEND_PORT" &
BACKEND_PID=$!

cleanup() {
    if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
        echo "Stopping local API server (PID $BACKEND_PID)"
        kill "$BACKEND_PID"
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo "Starting static site server at http://127.0.0.1:${PORT}"
echo "Press Ctrl+C to stop the server when you are done testing."
python3 -m http.server "$PORT"
