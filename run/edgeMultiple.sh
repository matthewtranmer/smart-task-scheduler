#!/usr/bin/env bash
set -Eeuo pipefail

# Determine paths
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null && pwd)"
SCRIPT="$ROOT/edge/edge-client.py"
PYTHON_BIN="$ROOT/env/bin/python"

export PYTHONPATH="$ROOT"
cd "$ROOT"

# Ask user how many instances to start (default: 1)
instances=""
while [[ -z "${instances:-}" ]]; do
  read -rp "How many instances do you want to start? [1] " instances || true
  instances="${instances:-1}"
  if ! [[ "$instances" =~ ^[0-9]+$ ]] || (( instances < 1 )); then
    echo "Please enter a positive integer." >&2
    instances=""
  fi
done

echo "Starting $instances instance(s) of $SCRIPT using $PYTHON_BIN ..."

pids=()
for (( i=1; i<=instances; i++ )); do
  "$PYTHON_BIN" "$SCRIPT" "$@" &
  pid=$!
  pids+=("$pid")
  echo "  - Started instance #$i with PID $pid"
done

# Show a summary and wait on children so Ctrl-C here stops all
echo "All $instances instance(s) started. PIDs: ${pids[*]}"
echo "Press Ctrl-C to stop; forwarding signal to children..."

cleanup() {
  echo
  echo "Stopping ${#pids[@]} instance(s)..."

  # First try SIGINT so Python raises KeyboardInterrupt
  for pid in "${pids[@]}"; do
    kill -s INT "$pid" 2>/dev/null || true
  done

  # Give them a moment to unwind context managers
  sleep 1

  echo "killing"

  # If any are still alive, escalate to TERM then KILL
  for pid in "${pids[@]}"; do
    kill -s TERM "$pid" 2>/dev/null || true
  done
  sleep 2
  for pid in "${pids[@]}"; do
    kill -s KILL "$pid" 2>/dev/null || true
  done

  wait
}
trap cleanup INT TERM
wait

