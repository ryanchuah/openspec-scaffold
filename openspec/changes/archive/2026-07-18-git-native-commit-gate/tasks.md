## 1. Git-native pre-commit hook

- [x] 1.1 Create `scripts/githooks/pre-commit` (bash, no extension): `set -euo pipefail`; resolve the
      repo root robustly (`REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"`, fall
      back to `dirname`-of-script two levels up when empty); exec `"$REPO_ROOT/scripts/check.sh"` and
      propagate its exit code so git blocks the commit on non-zero. No stdin/command parsing (git fires
      pre-commit only on real commits). Include a short header comment explaining it is the git-native
      primary layer that execs the single definition of green.
- [x] 1.2 `chmod +x scripts/githooks/pre-commit` (git tracks mode 100755; a non-executable hook is
      silently skipped by git — this exec bit is load-bearing).

## 2. Clone-safe wiring script

- [x] 2.1 Create `scripts/setup-hooks.sh` (bash, `set -euo pipefail`, executable): read the current
      value `cur="$(git config --local --get core.hooksPath 2>/dev/null || true)"`. If `cur` == 
      `scripts/githooks` → print "already configured", exit 0. If `cur` is empty → run
      `git config --local core.hooksPath scripts/githooks`, print confirmation, exit 0. If `cur` is any
      other non-empty value → print a WARNING naming `cur`, instruct the developer to reconcile, and
      exit non-zero WITHOUT overwriting. Guard the git calls so absence of git / not-a-repo prints a
      clear error and exits non-zero (never silently succeeds).

## 3. Fail-safe defer branch in test-gate.sh

- [x] 3.1 Extend the stdin-JSON Python guard in `scripts/test-gate.sh` so that a genuine commit
      carrying `--no-verify` (or a short-flag cluster containing `n`, i.e. a token matching
      `^-[a-zA-Z]*n[a-zA-Z]*$` but not `--…`, plus the literal `--no-verify`) among the post-`commit`
      argv is emitted as a **new single-line decision `GIT_COMMIT_NOVERIFY`** — reusing the existing
      single `$HOOK_DECISION`/`case` pattern (do NOT add a second output line). A `--no-verify`-free
      genuine commit stays `GIT_COMMIT`; `NOT_GIT_COMMIT` / `UNKNOWN` are unchanged.
- [x] 3.2 Add a new arm to the existing `case "$HOOK_DECISION"` (or an equivalent branch immediately
      after it), BEFORE the `check.sh` delegation. Defer (print a defer notice, `exit 0`, do NOT run
      check.sh) ONLY when the decision is exactly `GIT_COMMIT` (NOT `GIT_COMMIT_NOVERIFY`, NOT
      `UNKNOWN`) AND the git-native hook is confirmed active: `top="$(git rev-parse --show-toplevel
      2>/dev/null || true)"` non-empty; `hook="$(cd "$top" 2>/dev/null && git rev-parse --git-path
      hooks/pre-commit 2>/dev/null || true)"` resolves and `[ -x "$top/$hook" ]` (or `[ -x "$hook" ]`
      when absolute). `GIT_COMMIT_NOVERIFY` and `UNKNOWN` fall through to running check.sh (as does
      `GIT_COMMIT` when the hook is not confirmed). **Every git call in this branch MUST be guarded
      (`2>/dev/null || true`) so a git failure under `set -e` falls through to check.sh — never aborts
      (an abort exits ~128, which PreToolUse treats as non-blocking = silent gap).** Preserve all
      existing non-defer behavior byte-for-byte.

## 4. Automated tests

- [x] 4.1 Create `scripts/test_githook_pre_commit.py` (pytest, tmp_path). Build a throwaway git repo:
      `git init`; set user.email/name; copy the real `scripts/check.sh` and `scripts/githooks/pre-commit`
      into the workspace preserving structure + exec bits; write a repo-root `ruff.toml` (reuse the
      pattern in `test_check_sh.py`) and a clean `.py` file; write `scripts/test-cmd`;
      `git config --local core.hooksPath scripts/githooks`; make a seed `--no-verify` commit so the tree
      can be clean. Assert (all attempts use `--allow-empty`, which is verified to fire the hook):
      red `test-cmd` → `git commit --allow-empty` BLOCKED across spellings `git commit`,
      `cd <repo> && git commit`, `git -C <repo> commit`, `env FOO=bar git commit`; green `test-cmd` →
      `git commit --allow-empty` ALLOWED; `git commit --allow-empty --no-verify` with red `test-cmd` →
      ALLOWED (hook skipped). Also assert the **real** `scripts/githooks/pre-commit` in the repo is
      executable (guards against a lost exec bit).
- [x] 4.2 Extend the test-gate unit tests (add to `scripts/test_gate_command_detection.py` or a new
      `scripts/test_gate_defer.py`) covering the defer branch: with an executable pre-commit hook wired
      at `core.hooksPath` and a genuine `git commit` payload → `test-gate.sh` exits 0, prints the defer
      notice, and does NOT run check.sh (assert via a sentinel: e.g. a `test-cmd` that would write a
      marker file if check.sh ran — marker absent proves deferral). With `--no-verify` in the payload,
      or no hook wired → it runs check.sh (marker present / blocks on red). Reuse the existing
      workspace-builder pattern.

## 5. Manifest + instruction-surface updates

- [x] 5.1 Add to `scripts/scaffold_manifest.txt` (in sensible sections): `scripts/githooks/pre-commit`,
      `scripts/setup-hooks.sh`, `scripts/test_githook_pre_commit.py` (and
      `scripts/test_gate_defer.py` if that filename was used in 4.2).
- [x] 5.2 Update `tests/commit-gate-smoke/README.md` (NOT scaffold-managed — do not add to the
      manifest): add a section documenting the git-native layer — that `scripts/githooks/pre-commit`
      execs `check.sh`, is wired via `scripts/setup-hooks.sh` (`core.hooksPath`), fires on every commit
      spelling, is skipped by `--no-verify`, and is covered deterministically by
      `scripts/test_githook_pre_commit.py` (no gated session needed). Note that `test-gate.sh` now
      defers to it.
- [x] 5.3 Update `knowledge/reference/new-repo-bootstrap.md`: add a bootstrap step (near the existing
      hook-wiring step 1) to run `bash scripts/setup-hooks.sh` once per clone to wire
      `core.hooksPath`, explaining the git-native pre-commit hook is the primary agent-neutral gate and
      the `PreToolUse` test-gate is its Claude-only fallback.
- [x] 5.4 Update the `AGENTS.md` cross-agent-compatibility carve-out span (the paragraph naming the
      `PreToolUse` commit-test-gate hook as "the sole carve-out"): reword so the git-native
      `pre-commit` hook (tracked, agent-neutral, honored by every harness) is named the primary
      enforcement layer and the `PreToolUse` `scripts/test-gate.sh` hook is its Claude-only fail-safe
      fallback that defers to it. Keep it a shared span (edit here; it propagates). Do not expand the
      boot-read budget.

## 6. Dogfood + green suite

- [x] 6.1 Run `bash scripts/setup-hooks.sh` in THIS repo to wire `core.hooksPath` (the scaffold
      dogfoods the git-native gate). Confirm `git config --local --get core.hooksPath` == 
      `scripts/githooks`.
- [x] 6.2 Run `scripts/check.sh` (ruff check + ruff format --check + full pytest incl. `scaffold_lint`)
      and confirm it exits 0. Fix any ruff/format issues in the new Python test file. Also run
      `openspec validate git-native-commit-gate --strict` and confirm exit 0. Report the results;
      do NOT commit (the orchestrator commits).
