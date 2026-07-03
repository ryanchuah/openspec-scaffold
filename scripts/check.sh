#!/usr/bin/env bash
# check.sh — Single definition of green for OpenSpec repos.
#
# Runs in order:
#   (a) ruff check .
#   (b) ruff format --check .
#   (c) the test stage from scripts/test-cmd
#
# Exit conventions (byte-identical-across-repos):
#   0  → all stages passed
#   ≠0 → the first failing stage (named in the error message)
#
# Missing-tool degradation (mirrors test-gate.sh):
#   If ruff is not resolvable, warn on stderr, SKIP (a)+(b), continue to the
#   test stage. If scripts/test-cmd is absent/empty/the executable is
#   unresolvable, the test stage is a no-op (exit 0). Only a PRESENT tool
#   reporting a real violation, or a failing test, yields non-zero.

set -euo pipefail

CHECK_NAME="check"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || dirname "$SCRIPT_DIR")"
CMD_FILE="${SCRIPT_DIR}/test-cmd"

cd "$REPO_ROOT"

# ---- Stage (a)+(b): ruff check + format ---------------------------------
if command -v ruff >/dev/null 2>&1; then
    if ! ruff check .; then
        echo "${CHECK_NAME}: ruff check failed" >&2
        exit 1
    fi
    if ! ruff format --check .; then
        echo "${CHECK_NAME}: ruff format --check failed" >&2
        exit 1
    fi
else
    echo "${CHECK_NAME}: WARNING — ruff not found; skipping lint/format checks" >&2
fi

# ---- Stage (c): test stage ------------------------------------------------
if [ ! -f "$CMD_FILE" ]; then
    echo "${CHECK_NAME}: no scripts/test-cmd; test stage skipped (no-op)"
    exit 0
fi

CMD="$(cat "$CMD_FILE" | xargs echo -n 2>/dev/null || true)"

if [ -z "$CMD" ]; then
    echo "${CHECK_NAME}: scripts/test-cmd is empty/whitespace-only; test stage skipped (no-op)"
    exit 0
fi

EXECUTABLE="$(echo "$CMD" | awk '{print $1}')"
if ! command -v "$EXECUTABLE" >/dev/null 2>&1; then
    echo "${CHECK_NAME}: WARNING — cannot run '${CMD}' (config error) — NOT blocking" >&2
    echo "${CHECK_NAME}: resolve the test command in scripts/test-cmd or remove the file" >&2
    exit 0
fi

echo "${CHECK_NAME}: running '${CMD}'..."
if $CMD; then
    echo "${CHECK_NAME}: all checks passed"
    exit 0
else
    EXIT_CODE=$?
    echo "${CHECK_NAME}: tests failed (exit code ${EXIT_CODE})" >&2
    exit 1
fi
