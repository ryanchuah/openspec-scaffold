# notes — git-native-commit-gate (change-local scratch)

## Live probe results (git 2.43.0, throwaway repo /tmp/gitprobe) — VERIFIED 2026-07-18

These verify the git behaviors the fail-safe defer algorithm depends on. Re-runnable; see
design.md `### Live Probe`.

- **`git rev-parse --git-path hooks/pre-commit` honors `core.hooksPath`** — the authoritative,
  spelling-agnostic hook-path resolver:
  - `core.hooksPath` unset → `.git/hooks/pre-commit`
  - `core.hooksPath=scripts/githooks` → `scripts/githooks/pre-commit`
  - From a subdir it returns a **cwd-relative** path (`../scripts/githooks/pre-commit`) → the defer
    check must resolve the path from the worktree top (`cd "$(git rev-parse --show-toplevel)"` first),
    matching git's own hook-run cwd, then test `-x`.
- **The git-native pre-commit hook fires and blocks across ALL evasion spellings** — `git commit`,
  `cd . && git commit`, `git -C <repo> commit`, `env FOO=bar git commit` all ran the hook; with the
  hook exiting non-zero, only the `--no-verify` commit reached `git log`. Confirms the core premise:
  git-native closes the prefix-evasion + cross-agent gaps.
- **`git commit --no-verify` skips the hook** (no fire; commit succeeded) — the visible opt-out.
- **`git config --local core.hooksPath scripts/githooks`** writes repo-local scope.

## Fail-safe defer algorithm for test-gate.sh (resolves direction-gate 🔴)

Defer (no-op) ONLY when ALL hold; otherwise run `check.sh` (fail-safe toward running the gate):
1. Command classified **GIT_COMMIT** (positive) — NOT under the UNKNOWN fallback.
2. Command does NOT carry `--no-verify` / a short-flag cluster containing `n` (e.g. `-n`, `-nm`).
3. `git` resolves a work tree AND the hook `git rev-parse --git-path hooks/pre-commit` (resolved from
   the worktree top) exists and is executable.
Any failure/uncertainty (git absent, rev-parse fails, hook missing/not executable, UNKNOWN class,
`--no-verify` present) → run `check.sh`. Worst case = a double-run (mild); never a silent gap.

Rationale per gap:
- git-native not wired → don't defer → Claude-only fallback still gates (no regression).
- `--no-verify` present → don't defer → Claude still gates (matches today); git-native inherently
  skips `--no-verify`, so deferring would drop the gate.
- UNKNOWN → we're unsure it's even a commit → running check.sh is already the current fail-safe.

## Assumptions (non-blocking; batch-surfaced at operator gate)
- **A1:** git-native hook execs `scripts/check.sh` directly (single definition of green); no
  command-detection needed (git fires only on real commits). Default accepted.
- **A2:** `test-gate.sh` stays wired as PreToolUse (Option D fallback); NOT removed. Default accepted.
- **A3:** `scaffold_check.py` git-native adaptation is OUT of scope (separate follow-on) — it must not
  run in the golden source and must stay `--no-verify`-skippable. Default accepted.
- **A4:** New pre-commit hook + setup-hooks.sh are scaffold-managed (byte-identical downstream), added
  to the manifest. Default accepted.

## Apply routing
Operator pre-routed apply (and archive) to a **Sonnet subagent** for this session (instruction
2026-07-18: "For apply-executor and archive, use sonnet subagent instead of deepseek"). Legitimized by
AGENTS.md ("The operator MAY pre-route a specific change's apply to Sonnet-first"). Recorded here per
that rule.

## Follow-ons surfaced during this change
- `scaffold_check.py` has the identical prefix-evasion + Claude-only bypass class → candidate for
  git-native adaptation downstream (conditional: skip in golden source; keep `--no-verify` escape).
- Downstream `settings.json` may want the test-gate PreToolUse entry kept (as the fallback) — no edit
  strictly required by this change, but note during propagation.

## Verify checkpoint

**1. Verdict:** READY for archive. Self-review + pro behavioral pass + test-quality lens pass all
returned READY with zero defects; no fix cycles.

**2. Confirmed by eyeballing live output (behavior, not counts):** In throwaway repos with
`core.hooksPath` wired, the real git-native `pre-commit` hook BLOCKED a red-suite commit across every
evasion spelling (`git commit`, `cd && git commit`, `git -C … commit`, `env FOO= git commit`); a
`--no-verify` commit was ALLOWED (git skips the hook — the visible opt-out); a green commit was
ALLOWED. Fed a genuine `--no-verify`-free `git commit` payload, `test-gate.sh` printed
"git-native pre-commit hook is active — deferring (no-op)" and did NOT run check.sh; fed `--no-verify`
it ran check.sh itself. `setup-hooks.sh` behaved correctly across unset/already-set/conflict/not-a-repo.
This repo now dogfoods git-native (`core.hooksPath=scripts/githooks`).

**3. Defect found & fix (attributed):** None. No pass (self-review, pro, lens) surfaced a defect.

**4. As-built deltas (not already in artifacts):**
- The apply-executor added the defer-branch tests as a NEW file `scripts/test_gate_defer.py` (tasks 4.2
  allowed either that or extending `test_gate_command_detection.py`) and added it to the manifest.
- `scripts/test-gate.sh`'s Python guard now `import json, re, …` (the `re` import backs the
  short-flag `-n` cluster regex for `--no-verify` detection).
- The defer test's fixture uses a standalone helper script for `test-cmd` (created inside the test's
  tmp workspace, NOT a repo file) because `check.sh` word-splits `test-cmd` unquoted, mangling inline
  shell operators — a fixture-internal robustness choice, no repo impact.

**5. Forward-looking items to fold into knowledge/ at archive (recorded NOWHERE else):**
- **HANDOFF Priority 1 is now RESOLVED by this change.** At archive: mark
  `knowledge/questions/commit-gate-bypass.md` RESOLVED (this change) and remove its Parked pointer from
  `knowledge/questions/INDEX.md`; update `knowledge/HANDOFF.md` (Priority 1 done — Priority 2
  `custom-checks-family-fix` remains; either trim HANDOFF to just Priority 2 or re-park it and delete
  HANDOFF).
- **NEW follow-on — `scaffold_check.py` parallel bypass.** The scaffold-managed-file guard is *also* a
  prefix-anchored, Claude-only `PreToolUse` hook (same evasion class). Candidate for git-native
  adaptation downstream, BUT it must NOT run in the golden source (editing scaffold files is the point)
  and must stay `--no-verify`-skippable — so a byte-identical hook can't host it unconditionally.
  Park as a new question.
- **NEW monitored risk — silent degraded git-native state.** If `core.hooksPath` is set but the hook is
  later deleted or loses its exec bit, git-native silently stops firing (Claude's `test-gate.sh`
  fallback still gates Claude commits, but a non-Claude commit would be ungated). A future
  preflight/`facts` warning ("core.hooksPath set but pre-commit missing/not-exec") could surface it.
  Park as a monitored follow-on.
- **Downstream propagation (operator-gated).** New scaffold-managed files (`scripts/githooks/pre-commit`,
  `scripts/setup-hooks.sh`, `scripts/test_githook_pre_commit.py`, `scripts/test_gate_defer.py`) +
  modified `scripts/test-gate.sh`, `AGENTS.md`, `scripts/scaffold_manifest.txt` propagate byte-identical
  via `sync_scaffold.py` (`shutil.copy2` preserves the exec bit — verified). Per-repo manual sweep:
  each downstream must run `bash scripts/setup-hooks.sh` once; `new-repo-bootstrap.md` is scaffold-local
  (not synced) so the bootstrap step is repeated by hand; downstream `settings.json` may KEEP its
  test-gate `PreToolUse` entry (now the fallback). Add git-native-commit-gate to
  `knowledge/reference/pending-downstream-propagation.md`.
- **Accepted design notes (in design.md, restated for visibility):** git-native fires on `--amend`
  (incl. metadata-only) — accepted; `core.hooksPath` needs git ≥ 2.9 (older git → fail-safe fallback);
  `--no-verify` is a visible opt-out that fully bypasses the test gate for non-Claude agents (accepted,
  far better than silent prefix evasion).

**Still owned by archive (reconcile from this change dir — do NOT edit mid-verify):**
- `knowledge/STATUS.md` — add the git-native-commit-gate SHIPPED section (respect the ≤3 / cap rule).
- `knowledge/decisions/INDEX.md` — add the registry line for this change.
- `knowledge/questions/INDEX.md` — close the commit-gate-bypass Parked pointer (RESOLVED); add the two
  NEW follow-ons above (scaffold_check git-native; degraded-state monitor).
- `openspec/specs/commit-test-gate/spec.md` — promote the delta: ADDED requirements auto-applied by
  `apply_delta_spec.py`; the 3 MODIFIED requirements reconciled manually by the archive-executor.
- `knowledge/HANDOFF.md` — update per Priority-1-resolved above.
- `knowledge/reference/pending-downstream-propagation.md` — add this change.
