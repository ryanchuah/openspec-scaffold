#!/usr/bin/env bash
# test-gate.sh — Commit-test gate for Claude Code PreToolUse hook.
#
# Shared gate script (byte-identical across repos). The only per-repo value
# is scripts/test-cmd (one-line file; absent => gate is a no-op).
#
# Hook contract:
#   0  → allow commit (all checks passed, or no-op branch)
#   2  → block commit (checks failed)
#
# Hook-matcher guard (task 5.2): at the top of this script we read the
# PreToolUse hook's stdin JSON and extract .tool_input.command via python3.
# If the command is NOT a genuine `git commit` invocation, we exit 0
# (no-op) — this de-fangs the loose `Bash(git commit*)` if: matcher that
# can misfire on complex non-commit Bash commands. On unknown/unparseable
# stdin (including direct non-hook invocation), we fall through to run the
# gate (fail-safe).
#
# After the guard, delegation:
#   scripts/check.sh  →  exit 0 / ≠0


set -euo pipefail

GATE_NAME="test-gate"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ===================================================================
# Hook-command detection — skip non-commit commands (task 5.2)
# ===================================================================
# Read PreToolUse stdin JSON non-blockingly via python3.
HOOK_DECISION=$(python3 -c "
import json, sys, select

# Non-blocking read: check if stdin has data within 0.2s
r, _, _ = select.select([sys.stdin], [], [], 0.2)
if not r:
    print('UNKNOWN')
    sys.exit(0)

try:
    data = json.load(sys.stdin)
except Exception:
    print('UNKNOWN')
    sys.exit(0)

cmd = data.get('tool_input', {}).get('command', '')
if not cmd:
    print('UNKNOWN')
    sys.exit(0)

tokens = cmd.split()
# Strip leading env-var assignments (VAR=value) — they are not the command
idx = 0
while idx < len(tokens) and '=' in tokens[idx] and not tokens[idx].startswith('-'):
    idx += 1

if idx >= len(tokens):
    print('UNKNOWN')
    sys.exit(0)

if tokens[idx] != 'git':
    print('NOT_GIT_COMMIT')
    sys.exit(0)

idx += 1
# Skip git global options and their value arguments.
# Known value-consuming options: -c <name>=<value>, -C <path>.
# Options with embedded values (--git-dir=<path>) are handled
# because the whole token (e.g. '--git-dir=/repo') is skipped.
while idx < len(tokens) and tokens[idx].startswith('-'):
    # Options that consume the next token as their value
    if tokens[idx] in ('-c', '-C'):
        idx += 2  # skip the option and its value token
    else:
        idx += 1  # skip the option token itself

if idx < len(tokens) and tokens[idx].startswith('commit'):
    print('GIT_COMMIT')
else:
    print('NOT_GIT_COMMIT')
" 2>/dev/null || echo "UNKNOWN")

case "$HOOK_DECISION" in
    NOT_GIT_COMMIT)
        echo "${GATE_NAME}: command is not a genuine 'git commit' — skipping gate (no-op)"
        exit 0
        ;;
    GIT_COMMIT|UNKNOWN)
        # GIT_COMMIT → proceed with the gate.
        # UNKNOWN (fail-safe) → also proceed (never skip when unsure).
        ;;
esac

# ===================================================================
# Delegate to check.sh
# ===================================================================
CHECK_SCRIPT="${SCRIPT_DIR}/check.sh"

if [ ! -f "$CHECK_SCRIPT" ]; then
    echo "${GATE_NAME}: WARNING — scripts/check.sh not found; skipping gate (no-op)" >&2
    exit 0
fi

echo "${GATE_NAME}: running checks..."
if "$CHECK_SCRIPT"; then
    echo "${GATE_NAME}: all checks passed"
    exit 0
else
    echo "${GATE_NAME}: checks failed — commit BLOCKED" >&2
    exit 2
fi
