#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null && pwd)"
SCRIPT="$ROOT/edge/edge-access.py"

export PYTHONPATH="$ROOT"
cd "$ROOT"

exec "$ROOT/env/bin/python" "$SCRIPT" "$@"
