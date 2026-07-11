# Scaffold gap analysis — driven by downstream audit findings

**Status:** IN PROGRESS · started 2026-07-10 · orchestrator: Fable (Opus 4.8 1M)
**Resumable:** yes — this file is the anchor. A fresh session reads this first.

## Objective (from operator)

The operator ran substantive **correctness audits** on the two downstream repos
(`extrends`, `psc-monitor`) that this scaffold governs. Those audits surfaced many
gaps/bugs. Two questions:

1. **Gap analysis** — Given the classes of issue that surfaced downstream, are there
   gaps/weaknesses in *this scaffold* (its skills, gates, checks, rules) that could have
   **prevented** or **caught earlier** those issue classes? The scaffold decides how AI
   agents work in the downstream repos, so a systemic downstream failure pattern is
   evidence of a scaffold gap.
2. **Token-waste analysis** — Which scaffold procedures are burning tokens for low
   value? Example the operator posed: is self-review + deepseek-pro + deepseek-flash
   for the verify step of complex changes actually worth it?

**Role:** act as a departing principal engineer. Do judgment-heavy work now (detect
issues, lay long-term paths for senior engineers). At the **apply** step, PAUSE and tell
the operator whether fixes must be applied now to unblock, or can be parked. Record all
outstanding work in this repo, and state whether the apply/verify orchestrator for the
follow-up should be **Fable** or **Opus**.

## Hard constraints for this session

- Near session/token limits. **Prioritise planning + on-disk persistence** so work
  resumes cold in a new session without reloading this conversation.
- **Do NOT parallelise subagents** — if one runs out of quota mid-flight, only that one's
  work is lost, not all. Run subagents strictly sequentially.
- Use **haiku/sonnet subagents** for exploration/extraction (keep raw reading out of the
  orchestrator window); spend the orchestrator's tokens on judgment only.
- Do **not** mutate scaffold-managed files in this pass — this is analysis. Writing to
  `knowledge/research/` is fine.

## Where the source evidence lives

- **psc-monitor** correctness audit: `knowledge/research/correctness-audit-2026-07/`
  (FINDINGS.md ~4009 lines, CENSUS.md, CHARTER.md); test-quality audit:
  `knowledge/research/test-quality-audit/FINDINGS.md`; `knowledge/lessons.md`;
  audit-remediation changes (archive `2026-07-06-audit-*`, active `audit-remediation-wave-e1/e2`).
- **extrends** correctness audit: `knowledge/research/correctness-audit-2026-07/`
  (FINDINGS-wave1..4, ~5559 lines total); test audit: `knowledge/research/test-audit/FINDINGS.md`;
  `knowledge/lessons.md`, `knowledge/audit-log.md`; audit-correctness changes in archive.
- **scaffold** procedures: `AGENTS.md`, `.claude/skills/openspec-*/SKILL.md`,
  `.claude/skills/_shared/delegation-harness.md`, `checks.toml`, `scripts/`.

## Method

Sequential subagent runs, each distilling raw findings to a compact, judgment-ready
catalog written to THIS dir, returning only a short summary. Then the orchestrator does
the cross-cutting judgment.

## TODO / checklist (update status inline as work lands)

- [x] **A. Mine psc-monitor** → `psc-issues.md` DONE. 303 lines. Key signal: lessons
      written as prose (B5 livelock, F16 txn-visibility) never enforced as deterministic
      checks → identical bug recurred in sibling functions, re-found by hand months later.
      Per-change verify reviews one diff, never the accreted composition of many changes.
- [x] **B. Mine extrends** → `extrends-issues.md` DONE (405 lines — larger than psc-issues.md's
      304 because extrends has 4 correctness waves + a separate test-audit vs psc's 1 wave; 33
      merged defect classes after consolidating cross-wave duplicates). Key signal: agrees with
      and sharpens the psc-monitor signal — here the SAME failure shape (ground-truth silently
      destroyed on load failure; fail-soft branch with no operator-visible signal; wrong-boundary
      mocking) recurred *within the same multi-week audit program*, one wave apart, not months
      later as in psc-monitor. Also new: `decisions/INDEX.md § audit-first-remediation-deferred`
      means ZERO remediation has shipped for any of the 4 waves yet (unlike psc-monitor, which had
      partial remediation in flight) — every class in the file is still live in the codebase.
- [x] **C. Scaffold procedure/cost inventory** → `scaffold-procedures.md` DONE (229 lines).
      Per-tier full-model-pass counts SMALL≈4 / MEDIUM≈9 / COMPLEX≈14. Verify self→pro→flash
      run the IDENTICAL checklist (verify SKILL line 46), differentiated only by model weights.
      No mechanism enforces lessons-as-checks; composition detectors exist but off-by-default.
- [x] **D. SYNTHESIS** → `SYNTHESIS.md` DONE. 6 ranked gaps + honest non-gaps + preserve-list.
      Load-bearing claims re-verified against source (checks.py --list, verify SKILL 43–46).
- [x] **E. Token-waste judgment** → in SYNTHESIS.md (GAP 5 + verdict section). Answer: keep 2
      views, redirect the 3rd same-lens pass to a lens the stack lacks. Net cheaper AND better.
- [x] **F. OUTSTANDING-WORK.md** → DONE (6 items OW-1..6, tiers + Fable/Opus routing). Wired a
      High-priority pointer entry into `knowledge/roadmap.md` so the `outstanding` fact surfaces it.
- [ ] **G. Operator pause point** — reported in chat. Disposition: PARK ALL (nothing blocks this
      session). Orchestrator: Opus end-to-end for OW-1/OW-4; Fable design → Opus apply for the rest.

## Progress log (append-only; newest last)

- 2026-07-10: Terrain mapped. Findings sized. Plan written. Starting Run A.
- 2026-07-10: Run A (psc-monitor) done → psc-issues.md. Starting Run B (extrends).
- 2026-07-10: Run B (extrends) done → extrends-issues.md (405 lines, 33 classes). Ran sequentially
  per this file's hard constraint (5 subagent runs: wave1-4 + test-audit, sonnet, foreground,
  file checkpointed after each). Next: C (scaffold-procedures.md inventory), then D (SYNTHESIS.md).
- 2026-07-10 (later session, Fable): OW-2 (lesson-check-ratchet) lifecycle started per operator
  instruction (OW-1 explicitly NOT treated as prerequisite; pause at apply). Explore brief at
  `plans/lesson-check-ratchet/explore-brief.md`; prior-art + tooling research checkpointed under
  `openspec/changes/lesson-check-ratchet/research/`. Status tracked in OUTSTANDING-WORK.md (this dir).
- 2026-07-10 (same session): OW-2 propose COMPLETE — 4/4 artifacts frozen (5 pro review rounds,
  zero 🔴, all 🟡 fixed pre-freeze). PAUSED AT APPLY per operator instruction. Verdicts recorded in
  OUTSTANDING-WORK.md: parked apply does not block OW-3; apply/verify orchestrator = Opus (with a
  design-defect escalation caveat). Explore artifacts relocated into the change dir per D8.
- 2026-07-10 (later session, Fable): OW-3 (verify-stack-redirect) started per operator instruction
  (pause at apply). Explore COMPLETE: direction gate PREMISE: AGREE (round 1, zero 🔴, 🟡s resolved
  into brief). New empirical input: pass-yield mining — flash same-lens pass has zero recorded
  non-trivial unique catches across all 3 repos (~40 changes); full touch-surface inventory built
  (spec delta required: verify-multimodel-gate). Artifacts relocated into the change dir per D8:
  `openspec/changes/verify-stack-redirect/` (explore-brief, premise-review, research/).
- 2026-07-10 (same session): OW-3 propose COMPLETE — tasks.md + 2 spec deltas + notes.md acceptance
  criteria frozen (review round 1: PASS, PREMISE: AGREE, zero 🔴, both 🟡 fixed pre-freeze). PAUSED
  AT APPLY per operator instruction. Verdicts in OUTSTANDING-WORK.md: park OK (nothing blocks);
  apply/verify orchestrator = Opus, batch with OW-2's apply. Session also surfaced 3 new scaffold
  findings (validator blind spot for MEDIUM changes, no validate-at-freeze step, RENAMED promotion
  path unexercised) — recorded in OUTSTANDING-WORK.md "New findings".
- 2026-07-11 (later session, Fable): OW-5 (correctness-audit-skill) started per operator instruction
  (pause at apply). Explore COMPLETE: 4 parallel research extractions checkpointed under
  `openspec/changes/correctness-audit-skill/research/`; explore brief written; direction gate
  PREMISE: AGREE (round 1, zero 🔴, three 🟡 carried to design.md as implementation questions).
  Key evidence: psc-monitor ported extrends' audit playbook by hand (pattern already propagates
  unowned); 6 documented failure modes across both hand-rolled audits each mapped to a named
  mechanism in the skill direction. Status tracked in OUTSTANDING-WORK.md (this dir).
- 2026-07-11 (same session): OW-5 propose COMPLETE — 4/4 artifacts frozen (proposal 1 round AGREE;
  design 2 rounds, round 1 caught 2 real 🔴 incl. the untriaged-lint escape for REFUTED/one-off
  findings → per-wave-gate triage file; specs 2 rounds, 1 🔴 graduation-log gap; tasks 1 round).
  `openspec validate --strict` clean. PAUSED AT APPLY per operator instruction. Verdicts in
  OUTSTANDING-WORK.md: park OK (blocks nothing; OW-5 apply itself gated on OW-2 apply);
  apply/verify orchestrator = Opus with the standard design-defect escalation caveat. Recommended
  single Opus batch: apply OW-2 → OW-3 → OW-5. Two review invocations crashed operationally
  (budget-kill on first specs round; instant-kill on first tasks round) — both salvaged per the
  harness crash ladder with clean re-runs.
