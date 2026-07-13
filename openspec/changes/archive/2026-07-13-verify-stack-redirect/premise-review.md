## Review Round 1 — explore-brief (premise review)

### Summary

A well-researched, evidence-backed direction artifact. The brief argues that the verify phase's third pass (deepseek-v4-flash, running the identical behavioral checklist as self + pro) is a token-waste hotspot with near-zero unique defect yield, and that repointing it to a lens-diverse question (test-quality or data-scale) is a net upgrade at equal-or-lower cost. The evidence base (`pass-yield-evidence.md`, 40+ changes across 3 repos) is thorough and honestly caveated. The "lens as prompt, not detector" decision is the key architectural insight — it dissolves a dependency on unbuilt OW-1/OW-4 detectors and makes the redirected pass immediately valuable. The solution directly targets the root cause identified in SYNTHESIS GAP 5.

No direction-level defects found.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **Verifier agent body — unresolved design fork.** The scope framing (§5/`touch-surface.md`) says `.opencode/agents/openspec-verifier.md` "body must serve both behavioral and lens prompts." But the agent body today hard-codes "the same behavioral review the self-review performs" (as `touch-surface.md` L74-88 documents). The brief does not resolve *how* one agent body serves two fundamentally different prompts — parameterization in-body? A second agent file? An injected prompt prefix? This is a design decision the brief defers, but it has concrete implications: a second agent file = a new `dangling-skill-refs` surface and potential `noninteractive-delegation-safety` spec updates for the new file's permission posture. Recommend either (a) stating the resolution in the brief, or (b) explicitly flagging it as a deferred design.md decision with the known implications listed.

2. **Lens-pass recovery ladder — under-specified.** The brief says "Gate semantics preserved: lens pass is a hard gate on COMPLEX with the existing fix→re-run-failed-pass-and-after ladder and 3-cycle loop bound." But the existing ladder is shaped around two same-lens delegated passes (pro then flash). When the lens pass returns `NEEDS REVISION`, does the orchestrator fix and re-run *only* the lens pass, or the pro pass too? The "failed-and-after" semantics need clarification because the after-pass (lens) is now a different lens than the before-pass (pro behavioral) — re-running both may waste budget on a pass that already returned READY. Not blocking for explore, but worth noting before design.md is written.

### 💡 Suggestions

1. **Scope section could more explicitly name what "drift fixes" are mandatory vs. opportunistic.** The four "Drift fixed in passing" items are well-reasoned, but a reader might wonder whether items 2-3 (spec internal inconsistency + stale Task-tool language) are *required* for OW-3 to land cleanly, or are opportunistic cleanup that could be deferred to a separate change. The brief's analysis in `touch-surface.md` makes it clear these are adjacent but independent drifts — a one-line note in the scope section distinguishing "must-fix for this change" from "will-fix while here" would reduce ambiguity for the design.md author.

2. **Lens prompt quality vs. deterministic detector — implicit assumption.** The brief states the lens pass is "valuable now" as a prompt, and when OW-1/OW-4 detectors land they "feed the lens deterministic findings to confirm." This assumes a prompt-based lens catches *enough* to justify the token spend before detectors exist. Given the evidence that the same-lens flash pass catches nothing, any non-zero yield from a lens prompt is an upgrade — so the assumption holds. But an explicit acknowledgment that prompt-based lenses are a stepping stone (lower precision/recall than detectors) would strengthen the risk section. Not blocking.

### Verdict

PASS — ready to freeze and move to design.md

### Premise Verdict

```
PREMISE: AGREE
```
- The problem is real, evidence-backed, and correctly identified as redundant model breadth on the same lens.
- The root cause (single-axis pass differentiation; checklist never grew test-quality/data-scale questions) is correctly diagnosed.
- The solution (repoint the third pass to a lens the stack lacks, keep two same-lens views as the diversity guard) directly targets the root cause.
- The "lens as prompt" design dissolves a dependency chain and is forward-compatible with planned detectors.
- Evidence caveats (flash skipped in high-defect-density waves, verdict-strictness nuance) are honestly acknowledged and do not undermine the conclusion.
- Scope is well-framed with explicit in/out; no drift from the SYNTHESIS GAP 5 source.
