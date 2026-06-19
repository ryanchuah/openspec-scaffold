# Commit-Test-Gate Smoke

This directory contains a repeatable smoke procedure for the commit-test-gate
(`scripts/test-gate.sh`). The gate has two independently testable layers:

1. **Script layer** — `scripts/test-gate.sh` exit behavior across all five
   branches. Deterministic; can be run from any session.
2. **Hook wiring** — whether Claude's `PreToolUse` hook actually fires on
   `git commit`, and whether exit codes are correctly propagated. Requires a
   gated Claude session whose project dir carries the hook and a real
   `scripts/test-cmd`.

## Script-Layer Smoke Procedure

The snippet below exercises all five branches of `scripts/test-gate.sh` by
creating a temporary workspace with various `scripts/test-cmd` contents.
Expected exit codes are documented inline.

```bash
#!/usr/bin/env bash
set -uo pipefail   # NOT -e: cases below deliberately run commands that exit non-zero (the gate's exit 2)

# test-gate.sh resolves scripts/test-cmd relative to ITS OWN location (BASH_SOURCE),
# not the cwd — so copy it into a temp workspace and run the COPY, which then reads
# that workspace's scripts/test-cmd.
GATE_SRC="$(cd "$(dirname "$0")/../../scripts" && pwd)/test-gate.sh"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
mkdir -p "$WORKDIR/scripts"
cp "$GATE_SRC" "$WORKDIR/scripts/test-gate.sh"
GATE="$WORKDIR/scripts/test-gate.sh"

echo "=== 1. No test-cmd file (absent) -> exit 0 ==="
"$GATE"; echo "EXIT=$?"

echo "=== 2. Empty test-cmd -> exit 0 ==="
: > "$WORKDIR/scripts/test-cmd"
"$GATE"; echo "EXIT=$?"

echo "=== 3. Unresolvable executable (e.g. 'nonexistent-binary') -> exit 0 (WARNING) ==="
echo "nonexistent-binary --flag" > "$WORKDIR/scripts/test-cmd"
"$GATE"; echo "EXIT=$?"

echo "=== 4. Failing test command -> exit 2 (BLOCKED) ==="
echo "false" > "$WORKDIR/scripts/test-cmd"
"$GATE"; echo "EXIT=$?"

echo "=== 5. Passing test command -> exit 0 ==="
echo "true" > "$WORKDIR/scripts/test-cmd"
"$GATE"; echo "EXIT=$?"
```

If run from `tests/commit-gate-smoke/`, the output should be:

```
=== 1. No test-cmd file (absent) → exit 0 ===
test-gate: no scripts/test-cmd; skipping (no-op)
EXIT=0
=== 2. Empty test-cmd → exit 0 ===
test-gate: scripts/test-cmd is empty/whitespace-only; skipping (no-op)
EXIT=0
=== 3. Unresolvable executable (e.g. 'nonexistent-binary') → exit 0 (WARNING) ===
test-gate: WARNING — cannot run 'nonexistent-binary --flag' (config error) — NOT blocking commit
EXIT=0
=== 4. Failing test command → exit 2 (BLOCKED) ===
test-gate: running 'false'...
test-gate: tests failed — commit BLOCKED (exit code 1)
EXIT=2
=== 5. Passing test command → exit 0 ===
test-gate: running 'true'...
test-gate: tests passed
EXIT=0
```

## Hook-Wiring Smoke Procedure

This confirms Claude's `PreToolUse` hook (`.claude/settings.json`) actually
fires on `git commit`, propagates exit codes, and resolves
`$CLAUDE_PROJECT_DIR` correctly.

**Prerequisites:** a gated Claude session whose project directory carries:
- `.claude/settings.json` with the `PreToolUse` hook on `Bash(git commit*)`
  running `scripts/test-gate.sh`
- A real (non-empty) `scripts/test-cmd` file

**Do NOT run these in a production repo.** Use a throwaway clone or a scratch
repo.

### Check (a) — blocking commit on a failing test

```bash
# Set up a deliberately failing test command
echo "false" > scripts/test-cmd

# Attempt a trivial commit
git commit --allow-empty -m "smoke-test-fail"

# Expected: the hook fires, test-cmd runs and fails, git commit is BLOCKED.
# The error message appears in the Claude session output:
#   "test-gate: tests failed — commit BLOCKED (exit code 1)"
```

If the commit succeeds despite the failing test, the hook wiring is broken
(hook not loaded, exit code not propagated, or wrong path resolution).

### Check (b) — permitting commit on a passing test

```bash
# Restore a passing test command
echo "true" > scripts/test-cmd

# Re-attempt the commit
git commit --allow-empty -m "smoke-test-pass"

# Expected: hook fires, test passes, commit proceeds.
# Output: "test-gate: tests passed"
```

### Check (c) — `$CLAUDE_PROJECT_DIR` expansion

The hook references `scripts/test-cmd` relative to the project root. If the
hook uses `$CLAUDE_PROJECT_DIR` for path resolution, confirm it expands
correctly by adding a temporary diagnostic:

```bash
# Temporarily change the test command to print CLAUDE_PROJECT_DIR
echo 'echo "CLAUDE_PROJECT_DIR=$CLAUDE_PROJECT_DIR"' > scripts/test-cmd

# Attempt a commit
git commit --allow-empty -m "smoke-test-env"

# Expected: the output contains the full path to the project root.
```

**Note:** The hook-wiring smoke cannot be automated from a non-gated session
— it requires a Claude session whose project dir has the hook installed. It
is a documented operator-run procedure.
