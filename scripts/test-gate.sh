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
import json, re, sys, select

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
    # Scan the post-'commit' argv for --no-verify or a short-flag cluster
    # containing 'n' (e.g. -n, -nm, -vn) — git skips the pre-commit hook
    # for these, so the fail-safe defer branch must NOT defer on them.
    argv = tokens[idx + 1:]
    noverify = False
    for tok in argv:
        if tok == '--no-verify':
            noverify = True
            break
        if tok.startswith('--'):
            continue
        if re.match(r'^-[a-zA-Z]*n[a-zA-Z]*$', tok):
            noverify = True
            break
    print('GIT_COMMIT_NOVERIFY' if noverify else 'GIT_COMMIT')
else:
    print('NOT_GIT_COMMIT')
" 2>/dev/null || echo "UNKNOWN")

case "$HOOK_DECISION" in
    NOT_GIT_COMMIT)
        echo "${GATE_NAME}: command is not a genuine 'git commit' — skipping gate (no-op)"
        exit 0
        ;;
    GIT_COMMIT)
        # Positive genuine-commit classification, no --no-verify. Defer to
        # the git-native pre-commit hook ONLY if it is confirmed active
        # (existing + executable at the resolved core.hooksPath). Every git
        # call here is guarded (2>/dev/null || true) so a git failure
        # (absent / not-a-repo / bare) under `set -e` falls through to
        # running check.sh below — it must never abort the script (an abort
        # exits ~128, which PreToolUse treats as non-blocking = silent gap).
        top="$(git rev-parse --show-toplevel 2>/dev/null || true)"
        if [ -n "$top" ]; then
            hook="$(cd "$top" 2>/dev/null && git rev-parse --git-path hooks/pre-commit 2>/dev/null || true)"
            if [ -n "$hook" ]; then
                case "$hook" in
                    /*) hook_abs="$hook" ;;
                    *) hook_abs="$top/$hook" ;;
                esac
                if [ -x "$hook_abs" ]; then
                    echo "${GATE_NAME}: git-native pre-commit hook is active — deferring (no-op)"
                    exit 0
                fi
            fi
        fi
        # Hook not confirmed active — fall through to run check.sh.
        ;;
    GIT_COMMIT_NOVERIFY|UNKNOWN)
        # GIT_COMMIT_NOVERIFY → git will skip its own hook, so this gate
        # must run check.sh itself (preserves today's Claude coverage).
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
