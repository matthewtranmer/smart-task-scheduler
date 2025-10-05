#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SCRIPT="$ROOT/../edge/edge-access.py"

exec "$ROOT/../env/bin/python" "$SCRIPT" "$@"
