# Review Log — verify-stack-redirect

## Round 1 — 2026-07-10 — deepseek-v4-pro (openspec-reviewer) — tasks.md + both spec deltas + notes.md acceptance criteria

Now let me read the current promoted specs and the key source files in parallel:
Now let me read the verify SKILL and delegation harness §e, plus the research inventory:
Now let me check the AGENTS.md chain mentions and the research inventory:
Now I have all the context I need. Let me emit the review.

---

## Review Round 1 — tasks.md + spec deltas + acceptance criteria (verify-stack-redirect)

### Summary

High-quality artifacts with strong internal consistency. The tasks, deltas, and acceptance criteria are well-aligned: every delta requirement maps to concrete tasks, every acceptance criterion is traceable to tasks, and the recovery ladder semantics are correctly carried through all three surfaces. The noninteractive-delegation-safety corrective delta correctly removes the stale Task-tool exemption without touching permission posture. No 🔴 blocking issues found. Two 🟡 issues — a dangling cross-reference in the SMALL-tier AGENTS.md text, and task 5.1 references a chain-shape assertion that doesn't exist in lessons.md — and one 💡 suggestion about an unmentioned edit site (STATUS.md chain vocabulary) that the archive executor will encounter but the task list doesn't flag.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **SMALL-tier AGENTS.md cross-reference becomes dangling after the rename.** AGENTS.md "## Change tiers" SMALL bullet (currently L173-174) reads: `"SHALL run a single deepseek/deepseek-v4-flash verifier pass (same invocation shape as in the verify skill's flash pass)."` After this change, the verify SKILL no longer has a section or invocation block named "flash pass" — the old flash behavioral pass is removed; the new COMPLEX-only lens pass runs on flash tier but uses a fundamentally different checklist ("lens pass") and is not the invocation shape the SMALL verifier should emulate (SMALL still runs a behavioral review, not a lens review). Task 3.1 explicitly says "Do NOT alter the SMALL-tier rules in '## Change tiers'" — which leaves this cross-reference pointing at a name that no longer resolves. The SMALL flash pass behavior is unchanged and well-defined elsewhere, so this won't cause incorrect implementation, but it creates confusion and a stale reference in the authoritative tier-definition section. **Fix:** either (a) add a sub-bullet to task 3.1 updating the SMALL bullet's parenthetical to self-contain the invocation shape or point at a stable anchor (e.g. `"same invocation shape as the behavioral verifier pass"`), or (b) add a separate sweep task for this site.

2. **Task 5.1 references a non-existent lessons.md chain description.** The task says: "find the line describing the verify multi-model chain (§ mentioning 'self→pro→flash' or equivalent) and update it to the new tier-keyed shape." Inspection of `knowledge/lessons.md` shows no such line — the only verifier-related entry (L22, per-deliverable independent review) mentions `"a deepseek-v4-pro openspec-verifier pass"` as a singular technique, not the chain shape, and this singular pro-pass reference is still correct post-change (pro behavioral passes still run). The task will send the implementer hunting for something that isn't there, producing either a confused no-op or a mistaken edit. **Fix:** reword the task to say "check lessons.md for any chain-shape assertions and update if found; if no such line exists, note it and move on" — or drop it since there's nothing to update.

### 💡 Suggestions

1. **STATUS.md chain vocabulary is not in the edit inventory.** `knowledge/STATUS.md` L21 currently says `"self-review + pro + flash multi-model passes READY"` in a historical status entry. The explore-brief's touch-surface inventory correctly notes that STATUS.md is NOT an apply-time edit target (reconciled at archive). The task list correctly omits it. However, the touch-surface inventory's §7 coverage of the `knowledge/` tree (L250-306) mentions lessons.md, roadmap.md, and the questions file as needing attention — but STATUS.md's historical chain vocabulary is an adjacent mention an implementer might reasonably wonder about. Consider adding a one-line note in tasks.md §5 ("Repo docs") explicitly stating that STATUS.md chain vocabulary is archive-reconciled, not apply-edited, to prevent confusion during implementation.

### Internal Consistency Checks (all passed)

**Recovery ladder:** The delta requirement ("re-run the pass that failed and every pass after it"), task 1.5, and acceptance criterion #3 all describe the same semantics — MEDIUM: pro fails → re-run pro (it's the only/last); COMPLEX: pro fails → fix → re-run pro then lens; lens fails → fix → re-run lens only. The three-cycle escalation bound is preserved in all three. ✓

**Lens contract:** The delta's ADDED requirement (diff-scoped, no mandatory full-suite rerun, same verdict block, hard gate, MEDIUM opt-in, one-line rationale recording), task 1.4, and acceptance criteria #2/#3 agree on every clause. The "prompt-based stepping stone" / detector-handoff sentence is included in both the delta and task 1.4. ✓

**Recording rules:** The delta MODIFIED requirement 5 (lens + rationale recorded, attribution to "self-review, pro pass, or lens pass"), task 1.6, and acceptance criterion #3 all match. ✓

**No budget drift:** Task 2.1 preserves `780`/`-k 15` for both verifier rows; acceptance criterion #4 confirms budget-agreement green. All invocation budgets in task 1.2 match the §e table. ✓

**Verifier permission posture:** Task 4.1 says "Keep '## Your Review' itself, the Delegating-exploration, Data-safety, Prohibitions, and Verdict-Format sections unchanged"; task 4.2 says "Do not touch the permission: block." The noninteractive-delegation-safety delta preamble explicitly states "Permission-posture requirements are untouched." No weakening. ✓

**D10 drift check:** The explore-brief is PREMISE AGREE with no unresolved drift items. The tasks and deltas faithfully implement the direction described in the brief — same problem (redundant same-lens passes), same root cause (single-axis pass differentiation), same solution (repoint third pass to lens, keep two same-lens views). The scope does not creep beyond the edit sites inventoried in touch-surface.md. The one opportunistic scope inclusion (noninteractive-delegation-safety corrective delta) was explicitly called out in the brief as "will-fix-while-here" and is present in the delta. No PRÉCIS DISSENT. ✓

**MODIFIED requirement headers:** Every MODIFIED header in both deltas matches the promoted spec's exact requirement header text (verified by byte-level comparison against `openspec/specs/verify-multimodel-gate/spec.md` and `openspec/specs/noninteractive-delegation-safety/spec.md`). ✓

**SHALL/MUST and scenario format:** Every requirement in both deltas retains SHALL/MUST language. Every scenario uses `#### Scenario:` headers with WHEN/THEN/AND structure. ✓

**No accidental weakening of SMALL rules:** The delta's first modified requirement strengthens SMALL from "optional" (current promoted spec: "optionally one flash pass") to "REQUIRED" (matching AGENTS.md's existing mandatory language). No weakening. ✓

### Verdict

PASS — ready to freeze and move to apply. The two 🟡 issues (dangling SMALL cross-reference, imprecise task 5.1 description) are implementer-fixable during apply without requiring a re-review round, if the orchestrator is aware of them. Recommend noting them in the apply briefing.

### Premise Verdict

```
PREMISE: AGREE
```
- The problem and root cause are correctly carried through from explore-brief to tasks/deltas.
- No drift detected: scope matches the touch-surface inventory; solution faithfully implements the proposed direction.
- The one opportunistic inclusion (noninteractive-delegation-safety corrective delta) was explicitly pre-disclosed in the brief as "will-fix-while-here."

---
**Orchestrator disposition (Fable, 2026-07-10):** zero 🔴, PASS, PREMISE: AGREE → artifacts FROZEN.
Both 🟡 fixed in tasks.md BEFORE freeze (not deferred to apply): 🟡1 → task 3.1 now carries the
surgical SMALL-parenthetical fix (behavioral shape at flash tier, explicitly NOT a lens pass);
🟡2 → task 5.1 reworded to conditional verify-no-op with the reviewer's finding recorded. 💡1 →
task 5.1 now states STATUS.md chain vocabulary is archive-reconciled, not apply-edited.

**Lens selection for THIS change (recorded per the new rule, for when it is verified):** this is a
MEDIUM doc/skill-text change with no data path and no new tests beyond the existing suite — no
lens pass opt-in warranted; verify under current semantics = self + pro (see notes.md self-reference note).
