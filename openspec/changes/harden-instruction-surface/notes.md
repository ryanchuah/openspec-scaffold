# Verify notes — harden-instruction-surface

## Verify — 2026-06-16 — verdict: READY FOR ARCHIVE

Docs/instruction-only change; no code, no external-API surface, no test suite in the scaffold
(no `scripts/test-cmd`; commit-gate inert here). Behavioral review = diff read against design D1-D7 +
the grep-acceptance battery from design's Verification section + spec/task mapping. All clean.

### 1. Verdict
**Ready for archive.** 0 CRITICAL / 0 WARNING / 0 SUGGESTION. 11/11 tasks `[x]`; `openspec validate
--strict` passes; `git diff --stat` = exactly the 6 instruction files (proposal/design untouched).

### 2. What I confirmed by eyeballing the live (rendered instruction) output
- AGENTS.md `## Change tiers`: the new lead-in (without-grant → propose tier+plan & confirm before
  executing; with-grant → self-classify; operator-unavailable → don't execute, report & wait) ends
  with `:` and reads naturally straight into the SMALL/MEDIUM/COMPLEX bullets; the trailing
  one-line/push-auth/ladder-pointer paragraph is intact.
- AGENTS.md cross-agent-compat: the "hook-free" claim is gone; the replacement reads as a deliberate,
  Claude-only carve-out for the shipped commit-test-gate hook and points to the decisions.md carve-out
  — it explicitly says it does NOT weaken the harness-private-state ban.
- fast-track ladder: no "non-crash → Sonnet immediately" remains; it now points to the apply skill's
  declared-blocker triage ladder (consistent with line 34's "delegation mechanics identical").
- verify SKILL + config.yaml: the full-suite re-run now reads "prefer `scripts/test-cmd`, fall back to
  the documented command, never improvise; e.g. pytest"; the hand-fix threshold reads "one line" in
  both. research-fetch rule (d) reads identically to AGENTS.md §9; heading is "Four rules"; dead
  `output/fetch-measure.md` path gone. onboard: Verify checkbox gone, two "Real changes: delegate
  apply/archive" teaching notes well-placed.

### 3. Defect found and how it was fixed
**None.** Apply (deepseek-v4-flash, no fallback) landed all 11 edits matching design D1-D7 with zero
drift. One *false-positive* signal during apply triage: a `### NON-CONVERGENCE BLOCKER` string appeared
in the executor jsonl — confirmed to be echoed proposal/task text, not a declared blocker.

### 4. As-built delta vs. the artifacts
**None.** The executor kept "Scale process weight to risk:" as the bridge sentence into the tier
bullets — this is consistent with design D2's intent (preserve the bullet intro), not a new decision.

### 5. Forward-looking items (fold into ai-docs/open-questions.md at archive; decisions.md where noted)
- **Propagation backlog (HIGH).** This change is scaffold-only. `extrends` and `psc-monitor` still carry
  the identical stale text (hook-free line, fast-track ladder, hard-coded pytest, missing web rule (d),
  onboard Verify checkbox, "~2 lines"). There are now **TWO** scaffold changes awaiting propagation —
  `harden-delegation` and `harden-instruction-surface` — both ride on the single-source "change 2".
- **Web-research convention still duplicated (MED).** This change only made the two copies *agree*
  (added rule (d) to `research-fetch-convention.md`); AGENTS.md §9 ↔ `research-fetch-convention.md` are
  still two sources of the same rules. Full single-sourcing is deferred to change 2.
- **Other audit findings deliberately deferred (MED), not addressed here:** war-story narrative
  duplicated 3× and the model-assignment matrix ~5× (→ change 2 / single-source); the apply
  "Completion detection" block and the verify MANDATORY block bury the happy path under stacked
  exceptions (convolution, "M7"); onboard kept as a simplified teaching path (design D6b) rather than
  fully delegated, by deliberate decision.
- **Reference-rot watch (LOW).** `fast-track-workflow.md` now references the apply skill's ladder by
  path (`.claude/skills/openspec-apply-change/SKILL.md`); a rename/move of that skill must update this
  reference. (Recorded in design Risks.)

### Still owned by archive (do NOT reconcile here — the archive-executor does it from this change dir)
- **STATUS.md** — add the Done pointer to `openspec/changes/archive/<date>-harden-instruction-surface/`.
- **ai-docs/decisions.md** — record the new `tier-confirmation-gate` decision (non-fast-track agents
  confirm tier+plan before executing); note that AGENTS.md now acknowledges the commit-test-gate hook
  carve-out (reinforces the existing hook decision).
- **ai-docs/open-questions.md** — fold in Field 5 items above (propagation backlog; web-convention
  de-dup; deferred audit findings; reference-rot watch).
- **Spec promotion** into `openspec/specs/`: new `tier-confirmation-gate/spec.md`; merge the
  `apply-convergence-guard` (MODIFIED) and `commit-test-gate` (ADDED) deltas into their existing specs.
  (Reminder: promoted specs need a `## Purpose` section — `openspec validate` enforces it.)
- **Cleanup** — none pending beyond the standard archive move.
