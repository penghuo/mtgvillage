#!/usr/bin/env bash
# Run backend smoke test and serve the frontend for local development on macOS/Linux.
set -euo pipefail

PORT="${1:-8000}"

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

sys.path.insert(0, str(Path.cwd() / "scripts"))

from mtg_price_checker import MTGPriceChecker

checker = MTGPriceChecker()
stores = ", ".join(checker.stores.keys()) or "none"
print(f"Configured stores: {stores}")
PY

echo "Starting static site server at http://127.0.0.1:${PORT}"
echo "Press Ctrl+C to stop the server when you are done testing."
python3 -m http.server "$PORT"
