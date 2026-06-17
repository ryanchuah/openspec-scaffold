# Review log — fix-convergence-guard

## Review Round 1 — deepseek-v4-pro (openspec-reviewer) — 2026-06-17

**Verdict: NEEDS REVISION** — 3 🔴, 6 🟡, 4 💡. Reviewer ran clean (no agent
fallback; `## Review Round` + severity markers present). All line citations the
reviewer relied on were re-verified against disk before acting.

### 🔴 Blocking
1. **A3 git-diff over-counts** — `git diff --name-only HEAD` is cumulative, not
   per-attempt; accumulating it into `files_edited` double-counts a file edited
   once → **false STOP:b**. → **ACCEPTED.** Task 5 rewritten to count per-attempt
   *deltas* via stored per-file content fingerprints.
2. **A1 unconditional ceiling vs spec "Healthy iteration"** — `spec.md` scenario
   "Healthy iteration is not interrupted" (verified, spec.md:31-34) says
   different-signature attempts must NOT be stopped; an unconditional ceiling of
   5 violates it. → **ACCEPTED.** Redesigned: oscillation detection (S1→S2→S1
   alternation) as the primary A1 stop + a high absolute backstop ceiling (20),
   and a spec delta acknowledging the backstop.
3. **A2 key normalization misses relative↔absolute drift** — reusing
   `_normalize_signature` only strips leading-`/` tokens, so a relative node id
   doesn't map to the absolute one. → **ACCEPTED.** Key normalization now reduces
   the node id to `basename(file)::test` (strips ALL dir prefixes).

### 🟡 Should fix
4. A3 spec delta must be unconditional → **ACCEPTED** (5.3/6.1 de-gated).
5. A2 section-isolation underspecified → **ACCEPTED** (delimiters enumerated +
   N-line fallback specified).
6. A4 path regex under-constrained → **ACCEPTED** (concrete regex specified).
7. No automated A1 oscillation test → **ACCEPTED** (added unit-test task 4.x/7).
8. A3 agent-doc contract should be unconditional → **ACCEPTED** (folds into #4).
9. A2+A4 coupled; implement together → **ACCEPTED** (ordering note added; A4
   regex applies inside A2's scoped section).

### 💡 Suggestions
10. Add "Effort: ~N hours" per task → **DECLINED.** Reviewer claimed "per the
    AGENTS.md MEDIUM template," but AGENTS.md:141-142 mandates no such field
    (tasks.md + pro review + acceptance in notes.md only). False premise.
11. `REPO_ROOT` via `git rev-parse` for shared-across-repos robustness →
    **ACCEPTED** (use `git -C "$SCRIPT_DIR" rev-parse --show-toplevel` with
    `dirname` fallback).
12. `openspec validate` existence assumed → **NOTED** (CLI is used throughout the
    project; left as-is, fallback noted).
13. Note `decisions.md` `--editing` supersession → **ACCEPTED** (added to notes.md
    for archive reconciliation).

---

## Review Round 2 — deepseek-v4-pro (openspec-reviewer) — 2026-06-17

**Verdict: READY TO FREEZE** — 0 🔴. Reviewer ran clean (no fallback). Confirmed
all 3 Round-1 🔴 genuinely resolved and the 💡#10 decline correct (AGENTS.md
MEDIUM text mandates no per-task effort field). Three new non-blocking 🟡 + two 💡,
all folded in at freeze (no further review needed — 🟡-only on a clean verdict):

- 🟡#1 fingerprint method ambiguous → **FIXED.** Task 5.1 commits to SHA1 of
  working file bytes; dropped the `git diff -- <file>` alternative.
- 🟡#2 pre-edit vs post-edit semantic shift → **FIXED.** Task 5.2 documents the
  post-edit semantic; task 6.1 updates the spec rule-(b) wording "about to edit"
  → "has edited". Functional outcome identical (run stops before next task).
- 🟡#3 silent rule-(b) defeat when git unavailable AND `--editing` absent →
  **FIXED.** Task 5.3 adds a stderr warning when degrading with no coverage.
- 💡#4 missing `explore-brief.md` → **ADDED** (anchors the audit + verified
  on-disk line refs for cold-start resumability).
- 💡#5 A4 test should include an extensionless/trailing-slash path → **FIXED** in
  task 4.3.
- 💡#6 scrutinize flash's A4 test cases at verify → **NOTED** for the verify phase.

**FROZEN at Round 2.** Proceeding to apply.
