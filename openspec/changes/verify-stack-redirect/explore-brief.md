# Explore brief — verify-stack-redirect (OW-3)

**Date:** 2026-07-10 · **Author:** Fable (orchestrator) · **Tier:** MEDIUM (high blast radius)
**Backlog origin:** `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` OW-3,
implementing GAP 5 of `SYNTHESIS.md` (same dir).
**Research inputs (this dir, `research/`):** `touch-surface.md` (complete edit-site inventory),
`pass-yield-evidence.md` (empirical per-pass defect yield across all 3 repos).

## Problem

For MEDIUM/COMPLEX changes, the verify phase runs three passes — orchestrator self-review →
deepseek-v4-pro verifier → deepseek-v4-flash verifier — that execute the **identical checklist**
on the **identical inputs**, each independently re-running the full test suite. The verify
SKILL is explicit that the only differentiation is model weights ("Three independent views").
This is the single most expensive redundancy in the gate ledger (3× full-suite-rerun behavioral
review per verify cycle; MEDIUM ≈9, COMPLEX ≈14 total model passes).

**Empirical yield (from `research/pass-yield-evidence.md`, ~40 multi-model-verified changes
across openspec-scaffold, extrends, psc-monitor):**

| Pass | Unique non-trivial catches | Notes |
|---|---|---|
| Self-review | ~25, incl. every CRITICAL | the workhorse |
| Pro pass | 1 substantial (TOCTOU race) + 2 trivial | the one real model-diversity win |
| **Flash pass (3rd, same lens)** | **0** | 3 cosmetic/doc nits total, ever |
| Security gate (different lens) | caught a permission-bypass **both** model passes rated clean | lens > model |
| Simplicity gate (different lens) | ~15 real defects | lens > model |

Meanwhile both downstream repos ran expensive post-hoc correctness audits that found bug
classes (hollow tests, unbounded data loads) that walked through all three same-lens passes —
because **no pass asks those questions**. The stack over-buys model breadth and under-buys
lens diversity.

## Root cause

Pass differentiation was designed on one axis only (model weights). The checklist itself never
grew a test-quality or data-scale question, so adding models re-samples the same blind spots.
The two gates that DO differ by lens (simplicity, security) are precisely the ones with
outsized recorded yield.

## Proposed direction

**Keep two same-lens views as the diversity guard; repoint the third invocation at a lens the
stack lacks. Same-or-lower token budget, strictly more question coverage.**

1. **MEDIUM:** self-review → pro verifier pass. **Drop the flash same-lens pass.** MEDIUM
   retains three lens-diverse gates after the model pass (simplicity hard, security
   recommended-conditional) — it is not left thinner, it stops paying for a third copy of the
   same answer.
2. **COMPLEX:** self-review → pro verifier pass → **lens pass** (flash model, same read-only
   `openspec-verifier` agent, same verdict-block format and hard-gate semantics, but a
   **different fixed prompt** and **diff-scoped**: no mandatory full-suite rerun — pro already
   did that; its budget goes to the lens question).
3. **Lens menu (v1 — two lenses, orchestrator selects, records one-line rationale in
   `review-log.md`):**
   - **Test-quality / adversarial-oracle lens (default):** for each new/changed test, "would
     this test fail if the behavior broke — name the assertion that trips"; flag tautological/
     forced-green asserts, empty test bodies, self-mocking the module-under-test, discarded
     return flags, unfrozen clocks. (OW-1's lens wording, run as prompt-only until OW-1's
     detector ships.)
   - **Data-scale lens (for data-path-dominant changes):** which input domains are unbounded
     in production; any full-materialization on unbounded queries (`fetchall()` et al.);
     does the change need an at-scale run or a recorded bounded-domain argument. (OW-4's
     wording, prompt-only until its detector ships.)
   - **Forward-compatibility:** a lens is a *prompt*, not a *detector*. This dissolves OW-3's
     previously-stated dependency on OW-1/OW-4: the lens pass is valuable now, and when the
     OW-1/OW-4 detectors land they feed the lens deterministic findings to confirm instead of
     raw discovery.
4. **SMALL: unchanged.** Its single flash verifier is the only independent model pass at that
   tier — not redundant. (Explicit keep decision for AGENTS.md L169–174.)
5. **Platform parity retained:** both Claude Code and OpenCode run the identical per-tier
   chain (per the `tier-review-tightening` decision). On OpenCode the pro pass buys
   fresh-context/role independence more than model diversity; the evidence shows fresh-eyes
   independence, not model weight, is what pays — acceptable, and parity keeps the harness,
   lint (budget-agreement), and cross-repo reasoning simple.
6. **Gate semantics preserved:** lens pass is a hard gate on COMPLEX with the existing
   fix→re-run-failed-pass-and-after ladder and 3-cycle loop bound; re-run ladder text updated
   for the new chain shape. Verify-report and `notes.md` field-3 attribution vocabulary
   updates ("self-review, pro pass, or lens pass").
   *Recovery ladder, resolved (premise-review 🟡2):* the existing rule already covers the new
   shape — re-run the failed pass and every pass **after** it, never before it. Pro fails →
   fix → re-run pro, then lens. Lens fails → fix → re-run lens only (it is the last pass);
   the fix itself is independently re-verified from disk by the orchestrator per the existing
   defect path, so the READY pro verdict is not silently invalidated.
7. **Verifier agent body, resolved (premise-review 🟡1):** **single agent file, no second
   agent.** `.opencode/agents/openspec-verifier.md`'s body is generalized to "execute the
   fixed review prompt supplied by the invocation; default to the behavioral review when the
   prompt does not override it" — the invocation prompt is already the parameterization point
   today (the SKILL passes a fixed prompt per pass). Read-only posture, permissions, and the
   verdict-block contract are shared by both prompts, so no new `dangling-skill-refs` surface
   and no `noninteractive-delegation-safety` permission-posture addition for a new file.

### Drift fixed in passing (found during this exploration)

Split must-fix vs. opportunistic (premise-review 💡1):

- **Must-fix (part of the change itself):** Verify SKILL pass-sequence prose (L41–44) still
  claims OpenCode runs flash-only — contradicts its own invocation section and AGENTS.md;
  stale since `tier-review-tightening`. The section is the core rewrite target anyway.
- **Must-fix (spec pins the chain):** `openspec/specs/verify-multimodel-gate/spec.md` is
  internally inconsistent (prose says OpenCode flash-only; its own scenario says pro→flash) —
  the required spec delta supersedes both with the new chain.
- **Will-fix-while-here (separable, opportunistic):**
  `openspec/specs/noninteractive-delegation-safety/spec.md` still describes the abandoned
  OpenCode Task-tool verifier path — corrective delta alongside, deferrable without harming
  OW-3 if the reviewer objects to scope.
- **Will-fix-while-here:** the SKILL cites "the fixed verifier prompt from design D5" — a
  live skill pointing into an archived change's design.md. Inline the canonical
  behavioral-verifier prompt and the new lens prompts in the SKILL itself (the section is
  being rewritten regardless).

## Scope framing

**Edit sites (complete inventory in `research/touch-surface.md`):**
`.claude/skills/openspec-verify-change/SKILL.md` (core rewrite of the multi-model section);
`.claude/skills/_shared/delegation-harness.md` §e rows + two-pass phrasing (lockstep with the
SKILL or `scaffold_lint` budget-agreement fails; keep 780s/-k15 budgets to minimize churn);
`AGENTS.md` verifier-role paragraph + chain mentions; `.opencode/agents/openspec-verifier.md`
(body must serve both behavioral and lens prompts); spec deltas for `verify-multimodel-gate`
and `noninteractive-delegation-safety`. `openspec/config.yaml` needs **no** edit. No test
asserts the chain shape. All skill/agent/harness/AGENTS.md edits auto-propagate via the
manifest; specs + knowledge docs need the manual per-repo sweep at propagation time.

**Tier note:** MEDIUM per the backlog; propose emits `tasks.md` (+ acceptance criteria in
`notes.md`) **plus the two spec deltas** — a deliberate, disclosed deviation from
"tasks.md only" because the chain is pinned in a promoted capability spec and leaving it
stale would recreate exactly the drift this change cleans up. The pro reviewer reviews tasks
and deltas together.

**Out of scope:** OW-1/OW-4 detectors (separate changes; lens prompts here are designed to
consume them later); SMALL-tier chain; composition-audit cadence (OW-6); the near-duplicate
explore/propose premise reviews (accepted as low-cost in SYNTHESIS); any change to the
simplicity/security gates (they are the proven part of the stack).

## Risks & honest caveats

- **Weakening a load-bearing gate:** the strongest counterargument. Mitigations: the dropped
  pass has zero recorded non-trivial unique yield across 3 repos; COMPLEX keeps a third hard
  gate (repointed, not deleted); MEDIUM keeps pro + simplicity + conditional security.
- **Evidence caveat:** flash was skipped more often in the highest-defect-density COMPLEX
  audit waves, thinning its opportunity to demonstrate value. Judgment: the asymmetry stands —
  where flash DID run (~dozens of changes), it caught nothing non-trivial while lens-diverse
  gates caught critical defects.
- **Verdict-strictness nuance:** one recorded case where flash rated the same observation
  stricter than pro (NEEDS REVISION vs READY). The observation itself was not unique, and the
  orchestrator judges findings from disk regardless; noted, does not change the call.
- **Lens-pass quality on flash:** a lens prompt on a cheap model could produce noise.
  Mitigation: fixed prompts with concrete, mechanical questions (the OW-1/OW-4 shapes are
  precisely the mechanically-checkable kind); findings remain leads-to-confirm-from-disk.
  Explicit stepping-stone acknowledgment (premise-review 💡2): a prompt-based lens has lower
  precision/recall than the eventual OW-1/OW-4 detectors — but given the pass it replaces has
  zero recorded non-trivial yield, any non-zero lens yield is an upgrade; the detectors, when
  they land, raise the floor deterministically.

## Success criteria

- MEDIUM verify runs exactly 2 behavioral passes (self + pro); COMPLEX exactly 3 with the
  third lens-diverse; SMALL unchanged.
- No same-lens full-suite rerun beyond self + pro anywhere.
- All chain descriptions (SKILL, harness, AGENTS.md, specs, verifier agent body) agree —
  zero residual drift; `scaffold_lint` green.
- Lens prompts inline, canonical, and cite-able by OW-1/OW-4 when their detectors land.
