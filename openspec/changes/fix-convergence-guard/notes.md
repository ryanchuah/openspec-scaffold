# W3 — fix-convergence-guard · notes

## Tier & process
- **MEDIUM** → propose emits `tasks.md` only; this `notes.md` carries the
  acceptance criteria; one deepseek-v4-pro review before freeze; phase-gated
  (do not auto-advance to apply). Per AGENTS.md `## Change tiers`.
- **NOT manifest-changing** — every touched file is already in
  `scripts/scaffold_manifest.txt` (`_convergence.py`, `test_convergence.py`,
  `test-gate.sh`). W3 modifies content, not the manifest list. Per the
  consolidation plan W3 is "before W6 (preferred)" but not a W6 hard prereq.
- **Scope = all of A1–A5** (the audit's full convergence-fixes set). They are
  cohesive: A2+A4 are both signature quality, A1 is the oscillation backstop,
  A3 hardens the rule-(b) input, A5 is the commit gate's cwd. A5 is the most
  separable (different file, already W0-smoked) — a candidate to split out if
  review wants a smaller change, but it's a few lines and rides along cleanly.

## Provenance
- Findings: `ai-docs/workflow-audit-2026-06-16.md` §A1–A5; mapped to W3 in
  `ai-docs/consolidation-plan-2026-06-16.md` (ledger rows A1–A5, lines 166–170).
- Prereqs cleared: W0 hook smoke RESOLVED (exit-2-blocks + `$CLAUDE_PROJECT_DIR`
  proven; the A5 *cwd* case is the code fix W0 deferred here). W1, W2 SHIPPED.
- Apply order: W0 → W1 → W2 → **{W3, W4, W5}** → W6.

## Acceptance criteria
- **A1:** an oscillating-signature failure (S1→S2→S1…) with rotating/absent
  `--editing` ends in a declared `STOP:a:` (oscillation detected, or the absolute
  backstop ceiling), never a 600s wall-clock `timeout`/exit-124 crash — AND a
  genuinely progressing run with always-different signatures is NOT interrupted
  before the high backstop ceiling (spec "Healthy iteration" preserved).
- **A2:** unrelated churn in the test output (summary counts, other failures,
  warnings) does NOT change the targeted test's signature; a node id in either
  relative or absolute form maps to the SAME state key (basename-reduced).
- **A3:** rule (b)'s file-touch count is driven by the per-attempt *delta* of
  `git diff` fingerprints (cumulative diff does NOT double-count a once-edited
  file → no false STOP:b), so an executor that omits `--editing` still gets rule
  (b) enforced; a git error degrades gracefully to `--editing`-only (no crash).
- **A4:** two distinct errors differing only in a path-ish substring keep
  distinct signatures (no false STOP:a); cosmetic-only diffs still collapse.
- **A5:** with a resolvable `scripts/test-cmd` and a failing test, `test-gate.sh`
  exits **2** (blocks) even when invoked from a cwd ≠ repo root; no-op (exit 0)
  only when test-cmd is absent/empty or genuinely unresolvable.
- **Global:** `python3 scripts/test_convergence.py` green; the a/b/c blocker
  format, state-file layout, green/CONTINUE happy path, and the canary's forced
  declared-blocker behavior are all unchanged.

## Decisions resolved at Review Round 1
1. **A1 ceiling** — NOT an unconditional cap (that would violate the spec's
   "Healthy iteration" scenario). Resolved to: oscillation detection (S(n)==S(n-2)
   alternation, `attempts>=3`) as the primary stop + a high absolute backstop
   `_MAX_ATTEMPTS=20` so healthy iteration is never realistically interrupted.
2. **A3** — derive-from-git, but counting the per-attempt *delta* of file
   fingerprints (not the raw cumulative `git diff`, which would false-STOP:b).
   `--editing` becomes an optional hint; spec + both agent mirrors updated
   unconditionally.
3. **A5 split** — keep A5 in this change (a few lines, rides along cleanly; W3 is
   the convergence-correctness change and the cwd no-op is a convergence-of-trust
   gap). Not split.

## decisions.md reconciliation (for archive)
- `ai-docs/decisions.md` "Apply-executor convergence detection is offloaded to a
  deterministic helper" currently states the executor pipes `--editing <file>`
  as part of detection. After A3, `--editing` is an optional hint and the helper
  derives edited files from `git diff` deltas. Reconcile that decision's wording
  at archive (per AGENTS.md, decisions.md reconciliation happens at archive).
