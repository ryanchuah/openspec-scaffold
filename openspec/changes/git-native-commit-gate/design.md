## Context

The commit-test gate is enforced today only by a Claude Code `PreToolUse` hook on `Bash(git commit*)`
that runs `scripts/test-gate.sh` → `scripts/check.sh`. The matcher is a prefix-anchored glob, so
non-`git commit`-prefixed spellings (`cd repo && …`, `git -C … commit`, `env FOO= … commit`) skip it,
and `PreToolUse` is Claude-only so no OpenCode/DeepSeek agent runs it. `scripts/test-gate.sh` is
currently **git-free**: it parses the PreToolUse stdin JSON to classify the command, then delegates to
`check.sh`. `scripts/check.sh` is the single definition of green (`ruff check .` + `ruff format
--check .` + `scripts/test-cmd`), byte-identical across repos, with missing-tool degradation.
`.claude/settings.json` is per-repo (NOT scaffold-managed); `test-gate.sh` and `check.sh` ARE
scaffold-managed. A prior note in `scripts/scaffold_check.py:16` records that a git-native
`core.hooksPath` hook was "considered and rejected for W1" — but that was scoped to the
scaffold-managed-file guard (purpose: catch Claude's *accidental edits*), not the test gate, whose
cross-agent coverage is a load-bearing requirement.

## Goals / Non-Goals

**Goals:**
- Enforce the single definition of green (`check.sh`) on **every** `git commit`, regardless of command
  spelling and regardless of harness (Claude / OpenCode / operator terminal).
- Preserve defense-in-depth for the Claude path with **no double-run** in a normally-set-up clone and
  **no silent regression** when the git-native hook is not wired.
- Make the git-native layer **deterministically unit-testable** (no gated Claude session required).

**Non-Goals:**
- Adapting `scaffold_check.py` (the scaffold-managed-file guard) to git-native — it must NOT run in the
  golden source and must stay `--no-verify`-skippable; deferred to a follow-on.
- Downstream propagation and any downstream `.claude/settings.json` edits (operator-gated,
  post-archive).
- Retiring `test-gate.sh` — it is kept as the Option-D fallback.

## Live Probe

Verified against real `git 2.43.0` in a throwaway repo (`/tmp/gitprobe`) BEFORE finalizing the defer
algorithm — the design's correctness hinges on git's actual `core.hooksPath` resolution, so it was not
assumed. Commands and observed output:

```
$ git rev-parse --git-path hooks/pre-commit          # core.hooksPath UNSET
.git/hooks/pre-commit
$ git config --local core.hooksPath scripts/githooks
$ git rev-parse --git-path hooks/pre-commit          # honors core.hooksPath
scripts/githooks/pre-commit
$ (cd sub && git rev-parse --git-path hooks/pre-commit)   # from a subdir: cwd-relative
../scripts/githooks/pre-commit
```

With an executable `scripts/githooks/pre-commit` that `exit 1`s, commit attempts across every evasion
spelling were **blocked**, and only a `--no-verify` commit reached `git log`:

```
git commit                 → PRECOMMIT-FIRED, blocked
cd . && git commit         → PRECOMMIT-FIRED, blocked
git -C /tmp/gitprobe commit→ PRECOMMIT-FIRED, blocked
env FOO=bar git commit     → PRECOMMIT-FIRED, blocked
git commit --no-verify     → hook NOT run, commit succeeded (visible opt-out)
```

Extended probe (`/tmp/gitprobe2`, resolving the design-review 🟡s):

```
$ git commit --allow-empty -m x     # clean tree, no --no-verify
PRECOMMIT-FIRED → blocked (exit 1)   # the hook DOES fire on --allow-empty
$ (cd deep/er && top=$(git rev-parse --show-toplevel); \
   resolved=$(cd "$top" && git rev-parse --git-path hooks/pre-commit))
top=/tmp/gitprobe2  resolved=scripts/githooks/pre-commit  [ -x "$top/$resolved" ] → EXECUTABLE
# set -e trap: an UNGUARDED `top=$(git rev-parse --show-toplevel)` in a non-repo dir
#   → script dies exit 128 (PreToolUse treats non-2 as NON-blocking → silent gap!)
# GUARDED `top=$(git rev-parse --show-toplevel 2>/dev/null || true)` → falls through, exit 0
```

**Findings that shape the design:**
1. `git rev-parse --git-path hooks/pre-commit` is the authoritative, spelling-agnostic resolver of the
   hook path and **honors `core.hooksPath`** (relative or absolute). `core.hooksPath` has existed since
   git 2.9 (2016) — the effective minimum git version for the git-native layer; older git degrades to
   the fail-safe Claude-only fallback.
2. From a subdirectory `--git-path` returns a **cwd-relative** path → the defer check must resolve from
   the worktree top (git's own hook-run cwd) before testing `-x`. The combined cd-then-resolve pattern
   is probe-verified (Probe C).
3. `git commit --allow-empty` (clean tree, no `--no-verify`) **fires and is blocked** by the hook → the
   automated test can use `--allow-empty` for both the blocked (red) and allowed (green) cases without
   a false-pass risk (Probe A). This closes design-review 🟡1 (the unverified `--allow-empty` gap).
4. **`set -euo pipefail` trap (design-review 🟡2, probe-confirmed):** an unguarded `git rev-parse` in
   the defer branch, on failure (git absent / not-a-repo / bare), aborts `test-gate.sh` with exit ~128,
   which PreToolUse treats as **non-blocking → the commit proceeds ungated (silent gap)**. Every git
   command in the defer branch MUST be guarded (`$(cmd 2>/dev/null || true)`, or an `if` treating
   failure as "don't defer") so any git failure falls through to running `check.sh`. Load-bearing
   implementation requirement, not a stylistic note.
5. The git-native hook closes both gaps (all spellings fire; `--no-verify` is the only skip).

## Decisions

### D1 — The git-native hook execs `scripts/check.sh` directly; no command parsing
`scripts/githooks/pre-commit` is a small bash script that resolves the repo root and execs
`scripts/check.sh`, propagating its exit code (git blocks the commit on non-zero). Unlike
`test-gate.sh`, it needs **no** stdin/command parsing: git fires `pre-commit` only on genuine commits.
*Alternative rejected:* reuse `test-gate.sh` as the git hook — unnecessary (its command-detection
exists only to de-fang the loose PreToolUse matcher, irrelevant to git).

### D2 — Wiring via `git config --local core.hooksPath scripts/githooks`, conflict-safe
`scripts/setup-hooks.sh` is idempotent and conflict-safe:
- current value == `scripts/githooks` → no-op (report "already configured").
- current value unset/empty → `git config --local core.hooksPath scripts/githooks`.
- current value is some **other** path → **warn and abort WITHOUT overwriting**, instructing the
  developer to reconcile (they have custom hooks; the scaffold must not silently clobber them).
`--local` guarantees repo scope (never global). Raw `.git/hooks/` is not tracked/copied on clone, so
`core.hooksPath` pointing at the tracked `scripts/githooks/` is the clone-safe wiring.
*Alternatives rejected:* silently overwrite (destroys user customization); chain to the existing hook
(complex, out of scope). Warn-and-abort is least-surprise and loud.

### D3 — Option D: `test-gate.sh` defers to git-native, fail-safe (resolves direction-gate 🔴)
`test-gate.sh` gains an early branch, placed AFTER its existing command-classification block and
BEFORE it delegates to `check.sh`. It **defers (no-op, exit 0) ONLY when it positively confirms
git-native will run**; on any uncertainty it runs `check.sh` (fail-safe toward running the gate — a
false defer would be a silent gap, the one unacceptable failure).

**Defer iff ALL of:**
1. The command classified **`GIT_COMMIT`** (the positive branch) — NOT the `UNKNOWN` fallback.
2. The command carries **no** `--no-verify` and no short-flag cluster containing `n` (`-n`, `-nm`,
   `-vn`, …). The existing stdin-JSON Python guard is extended to emit this signal (it already
   tokenizes the command and skips global options; it now also scans the post-`commit` argv).
3. `git` is available AND resolves a work tree AND the hook path
   `git rev-parse --git-path hooks/pre-commit` (resolved from the worktree top,
   `cd "$(git rev-parse --show-toplevel)"`) exists and is **executable**.

Otherwise → run `check.sh` (unchanged path). This covers, by construction:
- git-native not wired (hook missing/not executable) → Claude-only fallback still gates → **no
  regression**.
- `--no-verify` present → git would skip the git-native hook, so `test-gate` must gate itself →
  **preserves today's Claude `--no-verify` coverage**.
- `UNKNOWN` classification / git absent / `rev-parse` failure → run the gate (already the current
  fail-safe posture).

Net: a normally-wired clone runs `check.sh` **at most once** per commit (PreToolUse defers → git-native
runs it). The defer message is printed to stdout so the deferral is observable.

**Implementation requirement — `set -e` safety (probe-confirmed, load-bearing):** `test-gate.sh` runs
under `set -euo pipefail`. Every `git` invocation added by the defer branch MUST be guarded so a git
failure (git absent, not-a-repo, bare) does NOT abort the script — an unguarded failure exits ~128,
which PreToolUse treats as non-blocking, silently skipping the gate. Use `$(git … 2>/dev/null || true)`
capture (or an `if git …; then` conditional) and treat any empty/failed result as "do NOT defer → run
`check.sh`." The defer branch's only exit-0 path is the positively-confirmed defer; all other paths
reach the existing `check.sh` delegation.

**Out-of-scope edge — `git -C <other-repo> commit` (design-review 🟡3):** the Python guard strips
`-C <other-repo>` as a global option and classifies `GIT_COMMIT`; the defer check then inspects the
*current* (orchestrator) repo, not `<other-repo>`. This matches the gate's long-standing scope — it has
always gated the orchestrator's own project repo (`check.sh` resolves its own repo root via
`BASH_SOURCE`, ignoring `-C`). A commit directed at a *different* repo is that repo's own gate's
responsibility. Accepted as out-of-scope; not addressed here.

*Alternatives rejected (from the explore-brief):* A keep-both-unconditional (double-runs `check.sh` on
well-behaved commits — perverse friction); B remove PreToolUse (a clone that skips setup has **no**
gate); C repurpose PreToolUse to an install-assert (orphans `test-gate.sh` + its tests/smoke).

### D4 — Deterministic automated test in a throwaway repo
`scripts/test_githook_pre_commit.py` builds a throwaway git repo under `tmp_path` (pattern reused from
`test_check_sh.py` / `test_gate_command_detection.py`): copies the real `check.sh` + the new
`pre-commit` into `scripts/`, provides a `ruff.toml` at the repo root + a clean Python file (so
`ruff format --check .` has something valid to scan) + a `scripts/test-cmd`, sets
`git config --local core.hooksPath scripts/githooks`, and makes a seed `--no-verify` commit so the tree
can be clean. Then asserts (all commits use `--allow-empty`, which is probe-verified to fire the hook,
so blocking is driven by `check.sh`'s result, not tree state):
- red `test-cmd` (or a staged lint violation) → commit **blocked** (non-zero `git commit`) across
  spellings `git commit --allow-empty`, `cd <repo> && git commit --allow-empty`,
  `git -C <repo> commit --allow-empty`, `env FOO=bar git commit --allow-empty`;
- green `test-cmd` + clean tree → `git commit --allow-empty` **allowed** (exit 0, commit created);
- `git commit --allow-empty --no-verify` → **allowed even when red** (git skips the hook — documents
  the visible opt-out).
Separately, extend the `test-gate.sh` unit tests to cover the D3 defer branch: with the git-native hook
present+executable and a `GIT_COMMIT` classification → `test-gate.sh` no-ops (exit 0, prints the defer
line, does NOT run check.sh); with `--no-verify` in the command, or the hook absent → it runs check.sh.

### D5 — Spec + AGENTS.md carve-out updates
Delta to `commit-test-gate/spec.md`: ADD two requirements (git-native pre-commit enforcement layer;
the PreToolUse test-gate's fail-safe defer) since they are genuinely new concerns; MODIFY three
existing requirements whose text is now stale — "Commits are gated" (enforcement now names git-native
primary + PreToolUse fallback), the smoke-fixture requirement (adds the deterministic automated test),
and the instruction-docs carve-out requirement (covers the git-native hook). MODIFIED entries are
reported (not auto-applied) by `apply_delta_spec.py`; the archive-executor reconciles them into the
main spec. AGENTS.md
cross-agent-compatibility carve-out (currently: *"the sole carve-out is the shipped commit-test-gate
`PreToolUse` hook … which runs the tracked, agent-neutral `scripts/test-gate.sh`"*) is reworded so the
git-native `pre-commit` hook (tracked, agent-neutral — honored by ALL harnesses, so it strengthens
rather than dents the cross-agent invariant) is the primary layer and `test-gate.sh` the Claude-only
fail-safe fallback.

## Risks / Trade-offs

- **[Silent degraded state]** `core.hooksPath` set but the hook file later deleted / loses its exec
  bit → git-native silently stops firing. → Mitigation: the fail-safe defer means Claude's PreToolUse
  fallback runs `check.sh` again (Claude stays gated); a future preflight/facts warning could surface
  the degraded state (noted as a follow-on, not built here).
- **[`--no-verify` visible bypass for non-Claude]** git-native inherently skips `--no-verify`; for a
  non-Claude agent there is no PreToolUse fallback, so `--no-verify` fully bypasses the test gate. →
  Accepted: this is an explicit, visible opt-out (vastly better than today's *silent* prefix evasion),
  and matches how `--no-verify` already works for the scaffold_check guard.
- **[Per-clone setup step]** `core.hooksPath` is `.git/config` state, not tracked/cloned, so
  `setup-hooks.sh` must run once per clone. → Mitigation: bootstrap-checklist step + idempotent script;
  the fail-safe means a forgotten setup degrades to today's Claude-only gate, not to nothing.
- **[`check.sh` scans whole working tree]** `ruff check .` covers unstaged files too — same as today's
  PreToolUse behavior; preserved, not a regression.
- **[`--amend` runs check.sh]** git fires the hook on `--amend` (incl. metadata-only) → `check.sh`
  runs. Correct (amends should gate); minor perf cost, accepted.

## Migration Plan

1. Land the new files + `test-gate.sh` defer branch + tests in the scaffold; run `setup-hooks.sh` in
   THIS repo so the scaffold dogfoods git-native; suite green (incl. `scaffold_lint`).
2. Update the `commit-test-gate` delta spec + AGENTS.md carve-out; archive syncs the delta to the main
   spec.
3. **Rollback:** the change is additive + fail-safe — `git revert` the commit(s); a repo can also
   locally `git config --unset core.hooksPath` to fall back to the PreToolUse-only gate at any time.
4. **Downstream (operator-gated, post-archive):** `sync_scaffold.py` propagates the new
   scaffold-managed files byte-identically; each downstream runs `setup-hooks.sh` once; the
   bootstrap-doc + spec sweeps are manual per-repo. Recorded in the pending-propagation ledger.

## Verification (change-specific acceptance criteria)

1. In a throwaway repo with `core.hooksPath=scripts/githooks`, a commit that fails `check.sh` (red
   `test-cmd` OR a ruff violation) is **blocked** across `git commit`, `cd && git commit`,
   `git -C … commit`, and `env FOO= git commit`; a green commit is **allowed**; `--no-verify` is
   allowed even when red. (Automated in `test_githook_pre_commit.py`.)
2. `test-gate.sh` **defers** (exit 0, prints the defer line, does NOT run check.sh) when the git-native
   hook is present+executable and the command is a `--no-verify`-free `GIT_COMMIT`; it **runs check.sh**
   when the hook is absent, when `--no-verify`/`-n` is present, or under `UNKNOWN`. (Automated in the
   test-gate unit tests.)
3. `setup-hooks.sh`: no-op when already `scripts/githooks`; sets it when unset; warns and **does not
   overwrite** a differing existing value; uses `--local`.
4. The scaffold's own `pytest` suite (incl. `scaffold_lint`) is green, and this repo has
   `core.hooksPath` wired (dogfooding).
5. `openspec validate git-native-commit-gate --strict` exits 0.

## Open Questions

None blocking. (Deferred, non-blocking: whether to add a preflight/facts warning for the silent
degraded state D-risk; whether/when to adapt `scaffold_check.py` to git-native downstream — both are
tracked as follow-ons, not part of this change.)
