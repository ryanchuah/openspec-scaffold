# review-log — defect-prevention-detectors (OW-1 + OW-4)

## Round 1 — tasks.md — `@openspec-reviewer` (deepseek-v4-pro), 2026-07-13

**Verdict:** NEEDS REVISION (two 🔴). **Premise:** `PREMISE: AGREE` (problem/root-cause/solution
sound; architecture decision confirmed correct given checks/*.py don't propagate).

### 🔴 (both fixed — re-review MANDATORY)
1. **T4 dispatch contradiction** — "mirror inventory special-case" vs "use `_normalize_finding_paths`":
   the inventory branch skips path normalization (zero findings), so following it verbatim would emit
   absolute paths and break the `_fingerprint` (repo-relative). → T4 REVISED: register detectors in
   `_BUILTIN_RUNNERS` and let the normal builtin `else` branch normalize + build the record
   uniformly; special-case ONLY `_availability_for_check` (T2).
2. **T4 runner return shape missing `findings` key** — `_execute_check` extracts `outcome["findings"]`
   for the aggregate `findings.json`; returning the record shape `{check,status,count,artifact}`
   would silently drop findings from the aggregate + baseline. → T4 REVISED: runner returns the
   OUTCOME dict incl. `findings` (the list), matching other `_BUILTIN_RUNNERS` entries.

### 🟡 (folded)
3. **`_PARSERS`/`--resume`** — the resume guard (~L1379) gates recovery on `_PARSERS` membership;
   without registering the detectors there, `--resume` silently drops their findings. → added to T4
   (register in `_PARSERS`, read the actual guard).
4. **self-mock `patch.object` limited to string-literal form** — common `patch.object(Mod, "x")` uses
   an `ast.Name` first arg, deliberately not detected (near-zero-FP over recall). → noted in T6.
5. **`SummaryLineFormatTest` filter tuple** — add the 2 names for format coverage. → added to T8.
6. **`unfrozen-clock` FP volume** — could be noisy; per-rule toggle is v2. → advisory-labeled in T6;
   deferred as notes.md A3.

### 💡 (folded)
7. `discarded-return-flag` message marked `advisory:` with a legit-use example. 8. T13 repo_lint
   note already scoped OPTIONAL. 9. T14 now explicitly expects `test_checks.py` self-findings.

**Blind spot (premise, not a defect):** the 2 noisy rules could push repos to disable the whole
detector; per-rule toggle is the v2 fix (A3). v1 ships all 6 rules, noisy 2 advisory-labeled.

## Round 2 — tasks.md — deepseek-v4-pro, 2026-07-13

**Verdict:** NEEDS REVISION (one NEW 🔴). **Premise:** AGREE. Round 2 CONFIRMED the revised T4
dispatch is correct against the actual `checks.py` (`_BUILTIN_RUNNERS` → else-branch at L1138-1147
normalizes paths + extracts `outcome['findings']`; `_PARSERS` guard at L1379).

### 🔴 (fixed)
1. **notes.md/T4 dispatch contradiction (NEW, self-inflicted by the R1 fix):** notes.md criterion 5
   still said "special-cased in `_execute_check` like inventory" — contradicting the revised T4. →
   notes.md criterion 5 rewritten to match T4 (dispatch via `_BUILTIN_RUNNERS`; special-case only
   `_availability_for_check`).

### 🟡/💡 (folded)
- R2🟡1: `_PARSERS[name]` is CALLED at ~L791 (`_PARSERS[name](result.stdout)`), so the value must be
  CALLABLE — T4 now specifies `lambda _stdout: []` (None would crash a future refactor route).
- R2💡1: T4 notes `count` is overridden + `artifact` ignored by the else-branch (`findings` is the
  only load-bearing key). R2💡2: T5 signature pinned (keyword-only bools, exactly one True).

## Round 3 — tasks.md + notes.md — deepseek-v4-pro, 2026-07-13

**Verdict: PASS — zero 🔴, zero 🟡. PREMISE: AGREE.** Confirmed criterion-5↔T4 agreement, callable
`_PARSERS` value, no new contradictions.

**FREEZE decision:** zero 🔴 + PREMISE AGREE → **FROZEN** after 3 rounds (2 real 🔴 dispatch-contract
bugs caught + fixed pre-apply — exactly the silent-bug class the pro review exists to catch).

**Apply routing:** deepseek-flash default (no Sonnet pre-route) — the tasks.md is now exceptionally
precise (pinned dispatch contract, exact `ast.*` node specs per rule, exact test fixtures), which
suits the mechanical executor. Backstop: the orchestrator will INDEPENDENTLY exercise the detectors
on its own fixtures at verify (NOT trust the executor's green tests) — mandatory here because a
test-quality detector shipping forced-green tests would be the maximally ironic failure.

## Verify — 2026-07-13

- **Apply (deepseek-flash, no fallback):** all 14 tasks, 420→ tests. Self-reported 24 advisory
  self-findings (later 13 after the hidden-dir fix).
- **Self-review (orchestrator INDEPENDENT exercise):** PASS. Built own fixtures — test-quality
  flagged all 6 rules at EXACT correct lines (assert-true@6, assert-or-true@10, empty-test@12,
  unfrozen-clock@17, self-mock@20, discarded-return-flag@25), ZERO findings on a clean test file
  (real detection — anti-irony PASS); data-scale flagged only non-test `.fetchall()`, skipped
  test-file fetchall. Scoping correct both directions.
- **Verify defect found + fixed (re-delegated, deepseek-flash):** `_iter_py_files` didn't exclude
  hidden dirs → scanned `.claude/worktrees/` (24→13 findings after fix). + tightened
  `test_all_rules_flagged` to exact-line assertions + added `test_hidden_dir_skipped`. Confirmed on
  the real repo: 0 hidden-dir paths; remaining 13 self-findings are all advisory (7 discarded-return
  + 6 unfrozen-clock), ZERO from the high-signal rules → scaffold's tests clean of real anti-patterns.
- **Pro behavioral verifier pass (deepseek-v4-pro):** **VERIFY: READY**. 5-dimension verification
  (suite green; AST logic traced correct per rule; dispatch/aggregate/resume wiring traced end-to-end;
  test oracles confirmed real not tautological; spec-delta mapping complete). 2 🟡 (self-mock dead
  code; fragile unfrozen-clock line assertion) — BOTH FIXED inline (trivial: dead-code deletion +
  membership assertion). Green re-confirmed (421 passed). No Sonnet fallback anywhere.
- **Simplicity gate:** satisfied (dead code removed). **Security gate:** not triggered. **Data-path
  rule:** N/A (this change adds detectors; it does not modify a data path).

**Verify verdict: READY → advance to archive (autonomy grant; no DISSENT/NEEDS-REVISION/operator gate).**
