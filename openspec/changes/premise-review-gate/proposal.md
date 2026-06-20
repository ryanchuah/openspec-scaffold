## Why

The most expensive thing to get wrong in a change is its **direction** — the problem
statement, the root cause, and whether the proposed solution actually addresses them — yet
that is the least-reviewed thing in the workflow. Two distinct blind spots exist:

1. **No one re-asks "is this the right thing to build at all?"** Once a `proposal.md` exists,
   the `@openspec-reviewer` audits its *coherence* ("is this well-formed, in-scope") and can be
   asked about its *premise* ("is this the right problem"), but a reviewer looking at a finished
   proposal is structurally anchored on *making that change good* — not on whether the change
   should exist. The bigger-picture decision (is this direction right, among the alternatives we
   weighed?) is made at the **explore** stage, and nothing downstream reviews it. Downstream steps
   review the change itself, never the question of whether the change is the wrong way to go.
2. **A SMALL change skips `propose` entirely**, so its direction-setting plan reaches `apply` with
   no independent pre-implementation review — only an informal operator nod and a *post-hoc*
   behavioral verifier that checks "did it match the plan," never "was the plan right."

The operator has been closing both gaps by hand, prompting the reviewer ad hoc to "agree with the
problem, root cause, and solution — and say what's missed." This change institutionalizes that, at
**two altitudes**: the direction (verified at explore, before any change is written) and the change
itself (verified at propose/apply, as today).

## What Changes

Introduce a **premise-review gate**: an independent, pre-implementation review of a change's
*direction* — problem / root cause / proposed solution + blind spots — written
**default-to-dissent** so it cannot decay into a rubber stamp. It is the pre-implementation
counterpart of the existing post-implementation `verify-multimodel-gate` (a single-pass *logical*
review of direction, vs. the verifier's multi-pass *behavioral* review). It applies at two altitudes:

- **Altitude 1 — the direction gate (NEW, all tiers).** Whenever the **explore** stage produces an
  `explore-brief.md` that will drive a downstream change, it MUST be premise-reviewed — the
  big-picture question, *"is this the right direction at all, among the alternatives?"* — before the
  operator advances to propose or apply. Run on the stronger model (`deepseek/deepseek-v4-pro`)
  because direction is where a wrong call is most expensive, regardless of tier. Details:
  - **Owner:** the **explore skill** invokes the reviewer itself, via `opencode run` using the same
    delegation harness the propose skill already uses (no new lifecycle step in `AGENTS.md`); it
    reports the resulting direction verdict to the operator before the phase advances.
  - **Trigger:** the brief is produced and reviewed when the operator signals intent to act on the
    exploration's conclusions — i.e. says "propose", "implement", "let's go", or similar advancement
    language. Explore keeps "no mandatory output"; the gate fires only at that point, not for idle
    thinking-aloud.
  - **File location + verdict sink** (exact choice deferred to design.md): explore usually runs before
    any change directory exists (the propose skill creates it), so the brief and its review output need
    a home — either create the change directory early, or write to a `plans/` directory and relocate
    during propose.
- **Altitude 2 — the change-itself checks (as before, kept).** These review whether the *specific*
  change is well-premised:
  - **SMALL** — a `deepseek/deepseek-v4-flash` premise pass over the plan (the full lens), after the
    plan is written and before apply delegation. If a pro-reviewed `explore-brief.md` exists, it is
    handed to the reviewer as context with an instruction to also flag any drift from the verified
    direction — same `PREMISE: AGREE|DISSENT` verdict, no separate mode.
  - **MEDIUM / COMPLEX** — the premise lens folded into the existing `deepseek/deepseek-v4-pro`
    `proposal.md` review (no new gate). The lens **always** runs; when a verified `explore-brief.md`
    exists, the review *additionally* cross-references it for drift. This is additive, not a
    replacement — the concrete proposal can surface blind spots the abstract brief did not.

Shared mechanics across both altitudes:

- **The premise lens** (the reviewer's checks): (1) is the stated problem **real and root**, not a
  symptom? (2) does the proposed **solution actually address that root**? (3) is the **scope**
  right-sized, and is what's-out stated? (4) what is the **blind spot**? Written so the reviewer
  states where the framing is *wrong* and why, rather than affirms it. Honest read-only caveat: the
  reviewer cannot run code (`bash: deny`), so it *reasons* about root cause and does not claim to have
  reproduced it (that remains verify's job).
- **A machine-readable verdict** — `PREMISE: AGREE` / `PREMISE: DISSENT` with cited concerns —
  **orthogonal to the 🔴/🟡/💡 severity system** (an artifact can be coherent, zero 🔴, yet draw a
  `DISSENT`). A `DISSENT` is never silently auto-resolved: it is surfaced to the operator for a
  direction decision (re-think / re-scope / explicit override-to-proceed).
- **Freeze interaction** (resolves the verdict-vs-freeze contradiction): for MEDIUM/COMPLEX the
  `proposal.md` artifact SHALL freeze only when its review returns **zero 🔴 AND `PREMISE: AGREE`**.
  (`design.md` / `tasks.md` keep the existing 🔴-only rule.)
- Propagate the rule through the scaffold (`AGENTS.md` shared spans, the affected skills and agent
  files) so downstream repos inherit it.

## Capabilities

### New Capabilities
- `premise-review-gate`: Independent pre-implementation review of a change's direction (problem, root
  cause, proposed solution, blind spots) at two altitudes — a pro **direction gate** on load-bearing
  explore output (all tiers) and the **change-itself** checks (flash for SMALL plans, folded into the
  pro proposal review for MEDIUM/COMPLEX) — emitting an `AGREE`/`DISSENT` verdict, with the reviewer
  mandate written default-to-dissent and read-only-honest, and `DISSENT` surfaced to the operator.

### Modified Capabilities
- `reviewer-budget`: its requirement states the `openspec-propose` workflow is "the only workflow that
  invokes the `openspec-reviewer`." This change adds two more invocation paths — the explore direction
  gate and the SMALL plan pass — falsifying that claim. The delta updates the requirement to cover all
  invocation paths under the same budget envelope (≥780s runaway backstop, `-k 15` soft-kill,
  incremental emission + partial salvage).

<!-- Interacted-with but NOT modified at the requirement level (documented in design.md, not delta'd):
     verify-multimodel-gate (post-implementation, distinct from this pre-implementation gate) and
     tier-confirmation-gate (the SMALL premise verdict feeds the existing operator checkpoint without
     changing its requirement text). -->

## Impact

- **`.claude/skills/openspec-explore/SKILL.md`** — NEW direction-gate wording: when the operator
  signals intent to proceed, capture conclusions as `explore-brief.md`, invoke the pro premise review
  (via `opencode run`, same harness as propose), and report the verdict before the phase advances.
- **`.claude/skills/_shared/delegation-harness.md`** — budget-table rows for the new invocation paths
  (explore direction gate on pro; SMALL plan pass on flash), under the existing 780s / `-k 15` envelope.
- **`.opencode/agents/openspec-reviewer.md`** — premise lens added to the mandate; `AGREE`/`DISSENT`
  verdict; anti-rubber-stamp + read-only-honesty framing; the lens covers an explore brief and a SMALL
  plan, not only `proposal.md`.
- **`.claude/skills/openspec-propose/SKILL.md`** — reviewer invocation requests the premise verdict for
  `proposal.md`; freeze requires zero 🔴 AND `PREMISE: AGREE`; `DISSENT`→operator branch; drift check
  against a verified explore brief.
- **SMALL flow** (`AGENTS.md` SMALL tier bullet + `.claude/skills/openspec-apply-change/SKILL.md`) —
  the flash plan premise pass + the apply-time gate.
- **`AGENTS.md`** — lifecycle/roles, tier descriptions, and the "After reading this file"
  acknowledgements name the two-altitude premise gate.
- **`openspec/specs/premise-review-gate/spec.md`** — new capability spec (both altitudes).
- **`openspec/specs/reviewer-budget/spec.md`** — delta for the added invocation paths.
- Scaffold propagation to downstream repos (scaffold-managed spans + skill/agent files).
- No application/runtime code; this is a workflow/process change. **Cost:** the direction gate adds one
  pro call **only when** explore produced a load-bearing brief; a SMALL change adds a flash plan pass
  (and the flash narrows to a consistency check when a pro-reviewed brief already covers the direction);
  MEDIUM/COMPLEX add no new call beyond the existing pro proposal review.
- **Calibration risk (resolved in design.md):** "default-to-dissent" must not become
  dissent-on-everything — dissent is for genuine direction faults, not style or taste.
