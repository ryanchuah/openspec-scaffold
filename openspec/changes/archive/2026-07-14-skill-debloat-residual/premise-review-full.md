Now I have a comprehensive picture. Let me emit the review.

---

## Review Round 1 — plans/skill-debloat-residual/explore-brief.md

### Summary

The explore brief correctly identifies four residual de-bloat items from OW-11 that share a single root cause: fuzzy prose rituals where a deterministic gate belongs. The problems are well-characterized and verifiable against the codebase — the verify skill's steps 13-14 do indeed prescribe keyword-search heuristics (lines 338-343, 356-361 of the verify SKILL), the explore skill's "Handling Different Entry Points" section (lines 196-297) is ~100 lines of worked-dialogue gallery prose with no mechanized effect, and the propose freeze ladder rests on a human read of free-text review output. Each proposed solution directly replaces fuzzy prose with a deterministic mechanism, and the scope is explicit about what is in and out. The COMPLEX tier is justified given the blast radius (three propagated skill surfaces, two genuine design calls, a new detector and a new script). No direction-level fault is present — the four problems are real, the root cause is correctly stated, and the solutions address it.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **Spec-delta target for verify de-bloat is uncertain and may be wrong.** The brief says (line 101) that verify de-bloat "may add/modify a `verify-multimodel-gate` requirement governing the artifact-mapping step's new shape." But the `verify-multimodel-gate` spec governs multi-model verification passes, lens selection, and simplicity/security gates — it does not govern the artifact/spec mapping checklist (currently verify steps 12-16), which lives entirely within the verify skill's own prose and has never been spec-gated. The de-bloat is fundamentally a skill-prose change, not a new capability needing a spec requirement. If a spec delta is genuinely warranted, it should name the correct spec or argue why it belongs in `verify-multimodel-gate` specifically. **Why it matters:** a design.md written against a wrong spec target will produce a delta that doesn't belong there, requiring a rework round at review or verify time.

2. **The structural coverage check's requirement↔task mapping mechanism is unspecified.** Item 1 proposes a deterministic cross-reference between delta spec requirements and `tasks.md` checkbox completion — but what is the mapping key? Requirement slugs? Keyword overlap? Manual annotation? Without a concrete mapping mechanism, the deterministic check risks being as fragile as the keyword-search it replaces (a requirement named "foo" won't match a task described as "implement the foo handler"). The brief acknowledges this is a "design call to settle in `design.md`" for item 3, but doesn't flag the same open design question for item 1. **Why it matters:** this is the single highest-risk design decision in the change — getting the mapping wrong produces false-positive CRITICALs (blocking verify on a non-existent gap) or false-negatives (missing a real gap), both of which would erode trust in the gate this change is supposed to harden.

### 💡 Suggestions

1. **The explorer-reviewer agent contract edit is an unstated dependency for Item 3.** The brief says item 3 needs a "companion prompt-template edit in the propose skill's reviewer-invocation section + the reviewer agent contract" — but the reviewer agent file (`.opencode/agents/openspec-reviewer.md`) is never named explicitly. The propose skill is listed in scope ("Skill-prose edits to verify/propose/explore"), but the reviewer agent is not. Since the reviewer agent is scaffold-managed and propagated, naming it explicitly in the "Skill-prose edits" line (line 102) would prevent a scope-surprise at design time. (Trivial to add — not a blocker.)

2. **L5 could be committed rather than design-gated.** The `checks.py --check <name>` output-dir fix (defaulting `--check` output under `output/checks/` instead of cwd) is simple enough that spending a design.md section on it may be overkill. The brief already notes it's "low-risk, improves every downstream detector." Committing to it at proposal time would simplify the design. (Judgment call — not a defect.)

3. **"Scope not yet concrete" for several design details — expected at explore altitude, not a fault.** Per D11, the under-specification in the structural-coverage mapping (🟡 #2), the FREEZE-token integration, and the exact spec-delta targets are all appropriate for explore and should be resolved in design.md.

### Premise Verdict

```
PREMISE: AGREE
- None — the four problems are correctly identified as instances of a single root cause (prose-as-enforcement is unreliable), the proposed solutions directly replace fuzzy prose with deterministic mechanisms, and the scope is well-framed with explicit out-of-scope items.
```

### Verdict

PASS — ready to advance to proposal. No 🔴 blocking issues. Direction is sound. The two 🟡 items (spec-delta target uncertainty and requirement↔task mapping mechanism) are design-time concerns that the proposal and design.md can resolve.