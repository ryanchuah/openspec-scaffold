#!/usr/bin/env bash
# test-gate.sh — Commit-test gate for Claude Code PreToolUse hook.
#
# Shared gate script (byte-identical across repos). The only per-repo value
# is scripts/test-cmd (one-line file; absent => gate is a no-op).
#
# Exit codes (probed in /tmp/gateprobe — see design.md Live Probe):
#   0  → allow commit (test-cmd absent, config error, or tests pass)
#   2  → block commit (tests failed)
#
# Per-repo convention:
#   scripts/test-cmd  — one-line file containing the test command to run,
#                        e.g. ".venv/bin/python -m pytest -q"
#                       Absent or empty/whitespace-only => gate is a no-op.
#                       Present-but-unresolvable => warning on stderr, exit 0
#                       (don't block commits on a fresh clone / config error).

set -euo pipefail

GATE_NAME="test-gate"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD_FILE="${SCRIPT_DIR}/test-cmd"

# --- No command file → no-op ---
if [ ! -f "$CMD_FILE" ]; then
  echo "${GATE_NAME}: no scripts/test-cmd; skipping (no-op)"
  exit 0
fi

# Read the test command, trimming whitespace
CMD="$(cat "$CMD_FILE" | xargs echo -n 2>/dev/null || true)"

# --- Empty/whitespace-only → no-op ---
if [ -z "$CMD" ]; then
  echo "${GATE_NAME}: scripts/test-cmd is empty/whitespace-only; skipping (no-op)"
  exit 0
fi

# --- Extract the executable name to check if it resolves ---
EXECUTABLE="$(echo "$CMD" | awk '{print $1}')"
if ! command -v "$EXECUTABLE" >/dev/null 2>&1; then
  echo "${GATE_NAME}: WARNING — cannot run '$CMD' (config error) — NOT blocking commit" >&2
  echo "${GATE_NAME}: resolve the test command in scripts/test-cmd or remove the file" >&2
  exit 0
fi

# --- Run the test command ---
echo "${GATE_NAME}: running '${CMD}'..."
if $CMD; then
  echo "${GATE_NAME}: tests passed"
  exit 0
else
  EXIT_CODE=$?
  echo "${GATE_NAME}: tests failed — commit BLOCKED (exit code ${EXIT_CODE})" >&2
  exit 2
fi
