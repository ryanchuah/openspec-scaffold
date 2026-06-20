# Verify notes — premise-review-gate

## 1. Verdict
**READY for archive.** All gates cleared: orchestrator self-review, pro verifier pass (READY), flash
verifier pass (READY), simplicity gate (clean), blocking behavioral smoke (passed). No security gate
(the change adds no auth/credentials/data/network surface — pure workflow documentation).

## 2. Live output eyeballed (behavior, not counts)
Ran the design's **blocking behavioral smoke**: a live `deepseek-v4-flash` premise pass (the real SMALL
plan-pass invocation) against a deliberately symptom-level plan — one that proposed masking slow-dashboard
*symptoms* with a loading spinner while explicitly ruling the slow queries (the root) out of scope. The
reviewer, reading the newly-installed mandate, returned **`PREMISE: DISSENT`** with correctly-reasoned
cited concerns: root/symptom conflation, solution-misses-root, a real blind spot, and the scope
contradiction (out-of-scope carved out the only fix). This confirms the gate can actually refuse a bad
direction — the core behavior this change exists to add — with the real model, not just on paper.

## 3. Defects found and how fixed
- **Reviewer-agent `### Premise Verdict` section rendered as code** — `.opencode/agents/openspec-reviewer.md`:
  the new section landed *inside* the "Example structure" fenced code block (the block's closer sat after
  the section), so the instruction rendered as example text. **Surfaced by:** orchestrator self-review
  (eyeballing the diff; `openspec validate` was green and blind to it). **Fixed by:** a re-delegated fresh
  deepseek-v4-flash apply-executor (closed the example fence after the `NEEDS REVISION` line, removed the
  orphan fence). Re-verified from disk: fences balanced, section renders as a real heading.
- **Stale acknowledgement count** — `AGENTS.md:345` lead-in said "Acknowledge **five** things" but a 6th
  item was added by this change. **Surfaced by:** the pro verifier pass (🟡). **Fixed by:** trivial
  one-word inline edit (`five` → `six`) — within the verify one-line exception; disclosed here.
- No logic/behavioral defects. No Sonnet fallback was needed at any point (apply, fix, and both verifier
  passes all ran the real deepseek agents).

## 4. As-built deltas vs. artifacts
None. The implementation matches proposal/design/specs/tasks. (Spec promotion of
`premise-review-gate/spec.md` + the `reviewer-budget` delta into `openspec/specs/` is **not** a delta — it
is an archive-phase operation by design; the executor correctly did not touch `openspec/specs/`.)

## 5. Forward-looking items (fold into knowledge/questions at archive)
- **Explore-altitude dissent calibration is unvalidated against real briefs (tune-after-real-runs).** The
  smoke confirmed `DISSENT` fires on a clearly-wrong direction, but the *false-positive* side — that the
  mandate's D11 calibration ("dissent only when demonstrably wrong, not merely under-specified") holds on
  real, thin explore briefs — has not been observed in production. Monitor the first real explore-gate
  runs; if it over-fires on under-specified-but-sound briefs, tighten the D11 wording.
- **Slug↔change-name relocation is best-effort and silently skips on mismatch.** If the operator explores
  under one topic slug but runs `propose` under a different name, the brief is not relocated and is
  orphaned in `plans/<slug>/`. Monitored risk; a future hardening could surface a warning when a
  `plans/*/explore-brief.md` exists but no slug matched at propose.
- **Minor cosmetic follow-ons (non-blocking, left for a future touch):** (a) explore `SKILL.md` step 2 says
  "(All-Altitudes, see design)" where it means "Altitude 1 direction gate"; (b) propose `SKILL.md` step 2
  picked up a 1-space list-marker indentation drift (renders fine).
- **Downstream scaffold propagation (rollout, not a code item).** `AGENTS.md` + the four skill/agent files
  are scaffold-managed; after this commits, `scripts/sync_scaffold.py <downstream-repo>` must be run per
  downstream repo to propagate, then reviewed/committed there.

## Still owned by archive
- Reconcile `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`, `knowledge/questions/INDEX.md` (fold in
  the field-5 items above).
- Promote `specs/premise-review-gate/spec.md` (new capability) and `specs/reviewer-budget/spec.md` (delta)
  into `openspec/specs/`.
- Cleanup: none pending (the smoke artifact `plans/_premise-smoke/` was already removed during verify).
