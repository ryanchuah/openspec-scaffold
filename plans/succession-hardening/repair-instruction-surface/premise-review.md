# SMALL premise review — repair-instruction-surface

**Reviewer:** `openspec-reviewer` via `opencode run --model deepseek/deepseek-v4-flash` (SMALL premise pass).
**Date:** 2026-07-03. **Plan reviewed:** `plans/succession-hardening/repair-instruction-surface/plan.md`.
**Portfolio direction:** already premise-gated `AGREE` (pro, 2026-07-02) — not re-litigated.

## Premise Verdict

```
PREMISE: AGREE
```

- Faithful to change 2 of the portfolio direction; all three sub-scopes map 1:1 to the explore
  brief and handoff. The one proposed expansion (config.yaml `context:`) is transparently flagged
  and left as an operator decision — a responsible flag, not silent scope creep.
- Problem/root-cause correctly instantiated ("golden source relies on prose only a frontier
  operator sustains" — a narrowing of the brief's "enforcement gap" root cause).
- Solution targets the root: content-preserving reorganization with the scaffold_lint SEAL as
  mechanical backstop, a proven zero-drift guarantee on the identity edits, and a source-verified
  exit-code reference.

## D10 drift assessment vs. explore-brief

- Reframed problem: none. Ruled-out approach reintroduced: none (synthetic-target dry-run is
  imposed by the sync freeze, not a rejected approach). Scope expansion: the config.yaml `context:`
  fill exceeds the brief's AGENTS.md-only wording, but is transparently flagged with a zero-drift
  proof and left to the operator. **No actionable drift.**

## Findings

- **🔴 Blocking:** none.
- **🟡 Should fix (1):** the plan's problem statement called `config.yaml` `context:` "entirely
  `<FILL:>`" when its Style and Web-research lines are already real content — risks an implementer
  overwriting live config. **RESOLVED** in the plan (now "partially `<FILL:>`: first four fields
  are placeholders; Style and Web-research are filled").
- **💡 (1):** if the config.yaml expansion is approved, the plan should give per-field fill
  guidance so the implementer doesn't invent content that contradicts AGENTS.md. → Carried to the
  operator confirmation as a decision; will add draft fill content to the plan if approved.
- **💡 (2):** process step 2 self-references "the SMALL flash premise pass" — which is THIS review.
  Sequencing note only, not a defect.

**Verdict: PASS — ready to proceed to apply delegation after the 🟡 fix (done).**
