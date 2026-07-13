# Premise review — composition-audit-cadence (direction gate)

**Date:** 2026-07-11 · **Reviewer:** deepseek-v4-pro via `opencode run --agent openspec-reviewer`
**Round:** 1 · **Reviewer-ran assertions:** no fallback-agent line in stderr; `### Premise Verdict` present.

## Reviewer findings (round 1)

**Summary (reviewer):** genuine structural gap — whole-repo *instruments* exist but no
whole-repo *occasions*; evidence base verified against cited digests; direction is the
smallest closing mechanism; frozen-contract boundary claims (OW-5 non-goal, OW-3
out-of-scope) verified against the artifacts. "The two concerns below are design-resolvable,
not direction-fatal."

- 🔴 Blocking: **none.**
- 🟡 1 — **Anchor namespace collision / silent clock reset:** reusing plain `audit/<date>`
  tags lets a run-audit tag (which runs no composition detectors) reset the composition
  cadence counter, silently masking composition debt.
- 🟡 2 — **"Cadence" vs pull-only tension:** the signal surfaces only in the pull-only
  `outstanding` fact; the word "cadence" implies periodic firing the mechanism doesn't
  deliver — tighten or reframe.
- 💡 1 — mixed-signal fallback (sparse archives vs commit volume) should be considered at
  design time. 💡 2 — consider a non-gating `knowledge_lint` staleness notice so the signal
  reaches CI/lint surfaces.

### Premise Verdict

```
PREMISE: AGREE
```

- Root, not symptom: ✅ · Solution targets the root: ✅ · Scope right-sized: ✅ (COMPLEX)
- Reviewer's overall note: NEEDS REVISION on the two 🟡 before design bakes in assumptions.

## Resolution (orchestrator, same session — 🟡s resolved into the brief pre-propose)

- 🟡 1 → brief §Proposed direction (1) rewritten: anchor is now a **composition-discriminable
  tag in the `audit/*` family**; a plain run-audit tag MUST NOT reset the composition clock;
  a composition anchor may count as a general audit anchor (superset). Exact tag/lint format
  → new open question 6.
- 🟡 2 → brief reframed to "advisory *staleness signal*, not a self-firing timer," with the
  v1 pull-surface stated plainly; a non-gating recurring-surface notice added as open
  question 5 (never a gate). Inverse risk ("signal unseen if pulls lapse") added to Risks.
- 💡 1 → folded into open question 3 (mixed-signal co-fire).
- 💡 2 → is open question 5.

Gate outcome: **PREMISE: AGREE, zero 🔴, both 🟡 resolved into the brief** — direction
advanced to propose per the operator's standing instruction for this session (work OW-6,
pause at apply).
