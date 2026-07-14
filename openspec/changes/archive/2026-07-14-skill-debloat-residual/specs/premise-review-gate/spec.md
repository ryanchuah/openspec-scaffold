## MODIFIED Requirements

### Requirement: A proposal freezes only on zero blocking issues AND premise agreement
For MEDIUM/COMPLEX, the `proposal.md` artifact SHALL freeze only when its review returns zero 🔴 **and**
`PREMISE: AGREE`. A `PREMISE: DISSENT` SHALL block the freeze regardless of severity count. The freeze
determination SHALL be mechanized rather than left to a human read of free-text review prose: the
`openspec-reviewer` SHALL emit its severity verdict as a strict machine-parseable line
`VERDICT: PASS` or `VERDICT: NEEDS REVISION` (a format tightening of its existing `### Verdict`; its
judgment is unchanged), where `VERDICT: PASS` denotes zero 🔴. A deterministic `scripts/freeze_check.py`
SHALL be the single canonical freeze determination: given the artifact type and the extracted review
text, it SHALL parse the last whole-line `VERDICT:` token (and, for `proposal.md`, the last whole-line
`PREMISE:` token) and derive a freeze verdict — `FREEZE: READY` iff `VERDICT: PASS` **and** (for a
proposal) `PREMISE: AGREE`; otherwise `FREEZE: BLOCKED` with a machine-distinguishable reason
(`needs-revision`, `premise-dissent`, or `missing-verdict`). A missing or unparseable `VERDICT` line, or
a missing `PREMISE` line on a proposal, SHALL fail closed to `FREEZE: BLOCKED — missing-verdict` (a failed
pass: do not freeze, re-run), never implicit agreement. The propose workflow SHALL gate the freeze on
`freeze_check.py` and route each `BLOCKED` reason to its handler — `needs-revision` to the mandatory-
re-review path, `premise-dissent` to the operator `AskUserQuestion` (re-frame / re-scope / override), and
`missing-verdict` to a review re-run. The orchestrator MAY overrule a demonstrably-false `BLOCKED` only by
recording the rationale in `review-log.md` (the existing "reviewer can be wrong" authority). `design.md`
and `tasks.md` SHALL retain the zero-🔴 freeze rule, likewise determined by `freeze_check.py` from the
`VERDICT` token (no `PREMISE` required for those artifacts).

#### Scenario: Clean but dissented proposal does not freeze
- **WHEN** a `proposal.md` review returns `VERDICT: PASS` but `PREMISE: DISSENT`
- **THEN** `freeze_check.py` emits `FREEZE: BLOCKED — premise-dissent`, the proposal does not freeze, and
  the dissent is surfaced to the operator for a direction decision

#### Scenario: Missing verdict token is a failed pass
- **WHEN** a `proposal.md` review omits a parseable `VERDICT:` line (or a proposal omits any `PREMISE:` line)
- **THEN** `freeze_check.py` emits `FREEZE: BLOCKED — missing-verdict` and the propose workflow re-runs the
  review rather than freezing

#### Scenario: Clean and agreed proposal freezes
- **WHEN** a `proposal.md` review returns `VERDICT: PASS` and `PREMISE: AGREE`
- **THEN** `freeze_check.py` emits `FREEZE: READY` and the proposal freezes and the workflow proceeds

#### Scenario: A design or tasks artifact freezes on the verdict token alone
- **WHEN** a `design.md` or `tasks.md` review returns `VERDICT: PASS`
- **THEN** `freeze_check.py` emits `FREEZE: READY` (no premise required) and the artifact freezes

#### Scenario: An orchestrator overrules a false block
- **WHEN** `freeze_check.py` emits `FREEZE: BLOCKED` on a finding the orchestrator confirms is false
- **THEN** the orchestrator MAY freeze only after recording the overrule rationale in `review-log.md`
