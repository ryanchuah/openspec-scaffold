# W3 — fix-convergence-guard · tasks

**Tier:** MEDIUM (tasks.md-only propose; acceptance criteria in `notes.md`).
**Scope:** close the five convergence-correctness holes from the workflow audit
(`ai-docs/workflow-audit-2026-06-16.md` §A1–A5) — make the deterministic guard
actually deterministic and make the commit gate fail-closed on a wrong cwd.

**Revised after Review Round 1** (deepseek-v4-pro, 3 🔴/6 🟡 addressed — see
`review-log.md`).

**Files touched (all already manifest-listed — NOT manifest-changing):**
- `scripts/_convergence.py` (A1, A2, A3, A4)
- `scripts/test_convergence.py` (A1, A2, A3, A4 regression tests)
- `scripts/test-gate.sh` (A5)
- `openspec/specs/apply-convergence-guard/spec.md` (spec deltas for A1/A2/A3/A4)
- `.opencode/agents/apply-executor.md` + `.claude/agents/apply-executor.md`
  (A3 `--editing` contract — kept byte-aligned)

**Behavior intent:** correctness fixes, not a redesign. The a/b/c trigger
taxonomy, state-file layout, and executor protocol stay the same; we tighten
*what trips* and *how robustly*.

---

## 1. A5 — `test-gate.sh` must run the test command from the repo root

The gate resolves `CMD_FILE` from `SCRIPT_DIR` (good) but then runs
`command -v "$EXECUTABLE"` / `$CMD` relative to the *current* directory
(`test-gate.sh:41,49`). A `.venv/bin/pytest` test-cmd silently no-ops
(exit 0 = gate disabled) when the PreToolUse hook fires with cwd ≠ repo root.

- [x] 1.1 Derive `REPO_ROOT` robustly (the file is "byte-identical across repos",
      so don't assume a fixed depth): `REPO_ROOT="$(git -C "$SCRIPT_DIR"
      rev-parse --show-toplevel 2>/dev/null || dirname "$SCRIPT_DIR")"`. `cd
      "$REPO_ROOT"` before the `command -v` / `$CMD` resolution so a repo-relative
      test-cmd (`.venv/bin/pytest`) resolves regardless of the hook's cwd.
- [x] 1.2 Keep the "unresolvable ⇒ warn + exit 0" config-error path (a genuinely
      missing venv must still not block a fresh clone). Preserve the exit-code
      contract exactly: 0 = allow (no-op / config error / pass), 2 = block
      (fail). No new exit codes.
- [x] 1.3 Smoke locally from a non-root cwd: with a resolvable `scripts/test-cmd`
      and a deliberately failing test, the gate exits 2 (blocks) when invoked
      from `/tmp`; with no `test-cmd`, exits 0. (Pairs with the W0 live-hook
      smoke, which proved exit-2-blocks but not the cwd case.)

## 2. A1 — stop oscillating failures with a declared blocker, not a wall-clock timeout

Rule (a) only fires on a *consecutive* signature match (`_convergence.py:197`).
An oscillating signature (S1→S2→S1…) with rotating/absent `--editing` trips
neither (a) nor (b), so the only backstop is the outer 600s `timeout` → exit 124
→ a wall-clock crash, NOT a declared `### NON-CONVERGENCE BLOCKER`.
**Constraint (Review #2):** the spec scenario "Healthy iteration is not
interrupted" (`spec.md:31-34`) requires that *different*-signature attempts keep
iterating — so the stop must NOT be a blunt "5 attempts then halt."

- [x] 2.1 **Oscillation detection (primary A1 stop).** Track the last *two*
      normalized signatures per test id in state (extend the per-failure record
      with `prev_signature` alongside the existing `last_signature`). When the
      current signature equals `prev_signature` (i.e. S(n) == S(n-2), an
      alternation like S1→S2→S1) and `attempts >= 3`, persist and return a
      declared `STOP:a:` whose detail names the oscillation (e.g. `…oscillating
      between two error signatures, not converging`). This catches the audit's
      named case without touching genuine forward progress.
- [x] 2.2 **Absolute backstop ceiling.** Add `_MAX_ATTEMPTS` set high enough to
      never interrupt plausible healthy iteration — propose **20** (review may
      tune). When `attempts >= _MAX_ATTEMPTS`, persist and return `STOP:a:` whose
      detail names the ceiling. This is the final guarantee that the run ends in
      a *declared* blocker rather than the 600s timeout, even for pathological
      patterns oscillation detection misses.
- [x] 2.3 Ordering: existing rule-(a) consecutive-match and rule-(b) checks run
      first (cleaner declared reasons win), then oscillation detection (2.1),
      then the absolute ceiling (2.2) as the catch-all.
- [x] 2.4 Update the spec (see task 6) so "Healthy iteration is not interrupted"
      acknowledges the absolute backstop ceiling, and add a scenario for the
      oscillation stop — keeping the spec and code consistent.

## 3. A2 — scope the signature and the state key to the failing test

`signature = _normalize_signature(raw_output)` normalizes the **entire** stdin
(`:271`), so unrelated churn (summary counts, reordered other failures,
warnings) changes the signature even when the targeted test fails identically →
rule (a) silently never matches on a real suite. Also `test_id` is used raw as
the state key (`:185,:264`) — a node-id format change splits the key.

- [x] 3.1 Add a helper that slices `raw_output` to just the failing test's
      section, then compute the signature over that slice. **Section boundaries
      (Review #5):** start at the line matching the failing `test_id` (reuse the
      patterns in `_extract_failing_test`); end at the *first* subsequent line
      matching any of: another test header (pytest `FAILED `/`::… FAILED`,
      unittest `FAIL:`/`ERROR`), a pytest separator run (`^=+ .* =+$` or
      `^_+ .* _+$`), or a summary line (`^=+.*(passed|failed|error).*=+$`).
      **Fallback:** if no end boundary is found, take up to N=40 lines after the
      start line. If the start line itself cannot be located, fall back to
      whole-output normalization (preserve current behavior as the floor).
- [x] 3.2 **Normalize the state key (Review #3 — do NOT just reuse
      `_normalize_signature`; its `/\S+` only strips leading-slash tokens).** Add
      a dedicated `_normalize_test_key(test_id)` that reduces the node id to a
      path-stable form: split on `::`, replace the file part with
      `os.path.basename(file_part)` so BOTH `/abs/tests/test_foo.py::test_bar`
      AND relative `tests/test_foo.py::test_bar` map to `test_foo.py::test_bar`.
      Use the normalized key for state; keep the raw `test_id` for the
      human-readable detail.
- [x] 3.3 Wire the scoped signature and normalized key into `_verdict`/`main`.

## 4. A4 — targeted path normalization + signature-quality tests

`re.sub(r'/\S+', ' <PATH> ', text)` (`:101`) runs first and eats *any*
`/`-led token, so two genuinely different errors differing only in path-ish
content collapse to one signature → rule (a) trips early = a **false** declared
non-convergence. (A2 made (a) too lax; A4 makes it too eager.)
**Coupling (Review #9):** A4's regex change applies *inside* A2's scoped
section — implement A2 (task 3) and A4 together on the same normalization
pipeline, A4's regex acting after A2's section isolation.

- [x] 4.1 Replace the greedy `/\S+` with a concrete path-shaped pattern that
      matches only real filesystem paths and leaves non-path `/` content (regex
      literals, URLs, math) intact. **Concrete regex (Review #6):**
      `r'(?:/[\w.\-]+)*/[\w.\-]+\.\w+'` — i.e. a `/`-separated run ending in a
      `name.ext` token. Keep the `/tmp/…` collapse working (it matches this
      pattern). Validate via the 4.3 tests; the regression scenarios are the
      acceptance bar, not regex perfection.
- [x] 4.2 Keep the strip ordering: A4's path regex still runs before the
      line-number/`:N` strip (the existing ordering comment at `:100-105` is
      load-bearing — preserve its rationale).
- [x] 4.3 Add regression tests to `test_convergence.py`:
      - distinct errors differing only in a path-ish substring stay **distinct**
        (the false-STOP:a guard);
      - cosmetic-only diffs (line/col/timestamp/hex/elapsed) still **collapse**
        (existing guarantee not regressed);
      - a non-path `/` token (e.g. a regex `a/b` in an error message) is NOT
        swallowed — include an extensionless path (e.g. `/usr/bin/python`) and a
        trailing-slash dir (e.g. `/tmp/build/`) in this case (R2 💡#5) to confirm
        the `\.\w+`-anchored regex leaves them intact.

## 5. A3 — derive edited files deterministically (per-attempt delta), not from flash

Rule (b)'s file-touch count is only as good as the optional `--editing <file>`
the executor self-reports (`apply-executor.md:37`). A flash executor that omits
it defeats (b). **Correctness (Review #1):** `git diff --name-only HEAD` is
*cumulative* — accumulating it raw would double-count a file edited once → a
**false STOP:b**. We must record the per-attempt *delta*.

- [x] 5.1 On each call, snapshot per-changed-file content fingerprints:
      run `git -C <repoRoot> diff --name-only HEAD` for the changed-file set,
      and for each file compute **SHA1 of the working file bytes** (R2 🟡#1 —
      commit to file-content hash; do NOT use `git diff HEAD -- <file>`, which is
      base-fragile). Store the `{file: fingerprint}` map in state.
- [x] 5.2 Compute the per-attempt delta: a file counts as "edited this attempt"
      iff it is newly in the changed set OR its fingerprint differs from the
      fingerprint stored on the previous call. Append only those delta files to
      `files_edited` (so rule (b)'s "edited 2+ times" reflects *distinct edit
      events*, not cumulative presence). Update the stored fingerprint map.
      **Semantic note (R2 🟡#2):** git-diff derivation is *post-edit* — the helper
      observes an edit that already happened, so rule (b) fires *after* the 3rd
      edit is detected rather than *before* a would-be 3rd edit. The functional
      outcome is identical (the run stops before the next task), but the spec's
      "about to edit" wording must be updated to "has edited" to match (task 6).
- [x] 5.3 Keep `--editing` as an optional supplement/fallback: when git is
      unavailable or returns nothing, fall back to the current `--editing`
      behavior. **Fail-safe:** any git/subprocess error must NOT crash the helper
      — degrade to `--editing`-only (a crash would surface as a rule-(c) gap).
      **Visibility (R2 🟡#3):** when degrading to `--editing`-only AND no
      `--editing` was passed (rule (b) then has zero coverage), log a one-line
      warning to stderr so the gap is visible in the execution log.
- [x] 5.4 **Unconditionally** (Review #4/#8 — `--editing` is now non-load-bearing)
      update the spec sentence and BOTH `apply-executor.md` mirrors (.claude +
      .opencode, kept byte-aligned): the helper derives the edited-file set from
      `git diff`; `--editing` is an optional hint, no longer load-bearing for
      rule (b).

## 6. Spec deltas (`apply-convergence-guard/spec.md`)

- [x] 6.1 Add/adjust scenarios: oscillation stop + absolute backstop ceiling, and
      amend "Healthy iteration is not interrupted" to acknowledge the backstop
      (A1); test-scoped signature + normalized key (A2); "distinct errors with
      path-ish diffs stay distinct" (A4); the A3 input change (git-diff-derived
      edits, `--editing` optional) — **unconditional** per Review #4. Also amend
      the rule-(b) "Repeated touch" scenario wording from "about to edit" to
      "has edited" to match the post-edit git-diff semantic (R2 🟡#2).
- [x] 6.2 `openspec validate apply-convergence-guard --strict` passes (spec name, not change name).

## 7. Verify

- [x] 7.1 `python3 scripts/test_convergence.py` — all existing + new tests pass
      (stdlib unittest; scaffold has no `.venv`, run with `python3`). New tests
      MUST include: an automated A1 oscillation case (alternating signatures for
      one test id → `STOP:a` at the oscillation/ceiling, Review #7), the A2
      scoped-signature + key-normalization cases (relative vs absolute node id
      maps to one key), the A4 path cases (4.3), and an A3 per-attempt-delta case
      (same file re-edited across attempts → STOP:b; different files → CONTINUE).
- [x] 7.2 Confirm no behavior change to the green/CONTINUE happy path or the
      a/b/c blocker format (regression: the canary in `docs/test/` still forces
      a declared blocker).
