# Premise review — outstanding-work-collector (direction gate)

Reviewer: `openspec-reviewer` (deepseek-v4-pro), synchronous direction gate over `explore-brief.md`.
Real-agent asserted (no fallback string in stderr; `### Premise Verdict` heading present).

### Premise Verdict

```
PREMISE: AGREE
- None
```

Verdict: **PASS — ready to move to propose.** No 🔴 blocking issues. The concerns below are
proposable details for the design phase; none indicates a direction-level fault.

## Reviewer summary

Strong brief. Diagnosis is sharp (the fusion of mechanical *gathering* with judgment-heavy
*prioritizing* into one hand-authored artifact is the root cause). Evidence is concrete and drawn
from real artifacts (stacked `UPDATE` banners, the rotted `go-live-readiness.md` triple-copy, the
stale `checks.toml` entry). Solution targets the root cause and correctly avoids the
already-tried-and-rotted "new centralized backlog doc." Scope and out-of-scope are well bounded.

## 🟡 Should fix (resolve or explicitly descope at propose)

1. **Quantify the prose-item gap.** If most real outstanding work lives in freeform prose
   (`questions/*.md` bodies, `plans/*`, audit `FINDINGS*` narrative), the gather's
   "structured-skeleton extraction" is marginal and the increment over the current subagent
   workaround is modest. **Mitigation:** at propose, sample the actual sources in extrends + psc to
   measure how much structure (checkboxes, bullet-pointers, IDs) exists vs. freeform prose — this
   decides whether skeleton-extraction is load-bearing.
2. **`plans/` convention is a hard dependency, not just an open question.** The gather cannot
   enumerate open work from `plans/` without a live-vs-archived convention, and none exists. Either
   resolve it concretely (e.g. `plans/archive/` subdir or a status marker) at propose, or descope it
   initially (gather treats all `plans/**` as "read this" until the convention lands).
3. **"Pull, never push" has no reminder mechanism.** The drift-checks catch structural rot but not
   the *accumulation* of new untriaged items. On-demand-only invocation could let a growing
   untriaged-Fable pile or an unchecked `tasks.md` box sit unnoticed. Is "the untriaged pile is
   itself a signal" sufficient if nobody looks? Flag as a design tension at propose.
4. **Fable's "predictable scanned location" is unspecified.** The untriaged-findings guarantee
   depends entirely on a real, machine-discoverable convention for where/how Fable writes findings.
   Resolve concretely at propose, or descope the untriaged bucket to "flagged for per-repo setup."

## 💡 Suggestions

1. **Fact-family "can't-fail" tension.** The gather parses several formats; if a parse step breaks on
   malformed input, does the fact degrade gracefully (partial results — undercutting the completeness
   guarantee) or fail (violating the fact-family "never fails" contract)? Acknowledge explicitly in
   design.
2. **Roadmap detection is genuinely new.** `knowledge_lint.py` doesn't currently scan
   `roadmap.md` semantically (only as a canonical-file orphan check). "Closed-but-unpruned roadmap"
   detection is a new capability needing its own design, not just a retired-token addition.

## Disposition

Direction is sound and gated PASS. The four 🟡 items are carried into the propose phase as design
inputs (esp. #1 quantify-the-gap and #2 the `plans/` convention dependency).
