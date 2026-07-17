## Purpose

Provide a pre-implementation premise-review gate — the direction-level counterpart to the post-implementation `verify-multimodel-gate` — that vets a change's problem statement, root cause, and proposed solution before implementation proceeds, at two altitudes: a pro direction gate on load-bearing explore output (all tiers) and change-itself checks (flash for SMALL plans, folded into the pro proposal review for MEDIUM/COMPLEX). The gate emits a machine-discriminable `PREMISE: AGREE|DISSENT` verdict, written default-to-dissent so it cannot decay into a rubber stamp, with `DISSENT` surfaced to the operator and never silently auto-resolved.

## Requirements

### Requirement: A premise-review gate vets a change's direction before implementation at two altitudes
The workflow SHALL include a pre-implementation **premise review** of a change's direction — its
problem statement, root cause, and proposed solution — distinct from and in addition to the existing
coherence review and the post-implementation `verify-multimodel-gate`. The premise review is performed
by the existing `openspec-reviewer` agent (no new agent) at two altitudes:
- **Altitude 1 — direction (all tiers):** when the explore stage produces an `explore-brief.md` that will
  drive a downstream change, a `deepseek/deepseek-v4-pro` review asks "is this the right direction at all"
  before the operator advances to propose or apply.
- **Altitude 2 — the change itself:** for MEDIUM and COMPLEX changes the premise lens is folded into the
  `deepseek/deepseek-v4-pro` `proposal.md` review; for SMALL changes it is a dedicated
  `deepseek/deepseek-v4-flash` pass over the plan before apply.

It SHALL NOT emit a premise verdict on `design.md` or `tasks.md` reviews (the premise is settled upstream).

#### Scenario: Explore direction gate reviews a load-bearing brief
- **WHEN** the explore stage produces an `explore-brief.md` on an operator advancement signal
- **THEN** a `deepseek/deepseek-v4-pro` `openspec-reviewer` pass assesses its direction and emits a premise verdict before the phase advances

#### Scenario: MEDIUM/COMPLEX premise review rides the proposal review
- **WHEN** the `proposal.md` of a MEDIUM or COMPLEX change is reviewed by `openspec-reviewer`
- **THEN** the review additionally assesses the premise and emits a premise verdict, with no separate gate or extra invocation

#### Scenario: SMALL premise review is a dedicated pre-apply flash pass
- **WHEN** a SMALL change has a written plan and has not yet been delegated to apply
- **THEN** the orchestrator runs one `deepseek/deepseek-v4-flash` `openspec-reviewer` pass over the plan and records its premise verdict

#### Scenario: Downstream artifacts are not re-litigated
- **WHEN** `design.md` or `tasks.md` is reviewed
- **THEN** no premise verdict is emitted and the existing severity-only review applies

### Requirement: The reviewer emits a premise verdict orthogonal to the severity system
The reviewer SHALL emit a premise verdict when reviewing a direction artifact — an `explore-brief.md`, a
`proposal.md`, or a SMALL plan: a
`### Premise Verdict` section containing exactly one line, `PREMISE: AGREE` or `PREMISE: DISSENT`,
followed by cited concerns (or `- None`) — in addition to, and independent of, its existing
`PASS`/`NEEDS REVISION` severity verdict. An artifact MAY be coherent (zero 🔴) yet draw a
`PREMISE: DISSENT`. The premise mandate SHALL be written **default-to-dissent**: the reviewer states
where the framing is wrong and why, and does not manufacture agreement; `DISSENT` is reserved for
genuine direction faults (symptomatic problem, solution missing the root, materially wrong scope, or a
critical missed consideration) and not for style, taste, or wording.

#### Scenario: Coherent artifact with a wrong premise
- **WHEN** the reviewer finds no 🔴 severity issue but judges the problem to be a symptom rather than the root cause
- **THEN** it emits `PREMISE: DISSENT` with the cited root-cause concern, independent of the severity verdict

#### Scenario: Sound direction
- **WHEN** the reviewer cannot fault the problem, root cause, or proposed solution
- **THEN** it emits `PREMISE: AGREE` and does not manufacture objections

#### Scenario: Non-direction issues do not trigger dissent
- **WHEN** the reviewer's only concerns are style, wording, or taste
- **THEN** those remain severity findings (🟡/💡) and the premise verdict is `PREMISE: AGREE`

### Requirement: The reviewer reasons about root cause read-only and does not claim empirical proof
The premise mandate SHALL state that the reviewer is read-only (`bash: deny`): it reasons about root
cause by reading the code, and SHALL NOT claim to have reproduced, confirmed, or empirically verified a
root-cause or behavioral assertion. Empirical confirmation remains the verify step's responsibility.

#### Scenario: Reviewer does not overclaim
- **WHEN** the premise review turns on whether a described cause is the real one
- **THEN** the reviewer reasons from the code it can read and explicitly does not assert empirical confirmation it cannot perform

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
(`needs-revision`, `premise-dissent`, or `missing-verdict`). The whole-line parse SHALL tolerate optional
`**` markdown emphasis around the token and/or its value — `**VERDICT:** PASS`, `**VERDICT: PASS**`, and
`VERDICT: **PASS**` SHALL all parse identically to `VERDICT: PASS` (and likewise `**PREMISE:** AGREE`,
`**PREMISE: AGREE**`, `PREMISE: **AGREE**` identically to `PREMISE: AGREE`) — while remaining strictly
line-anchored: a `VERDICT:` or `PREMISE:` token appearing mid-prose, rather than alone on its line
(allowing only the tolerated `**` emphasis and surrounding whitespace), SHALL NOT be accepted as a parsed
verdict. A missing or unparseable `VERDICT` line, or a missing `PREMISE` line on a proposal, SHALL fail
closed to `FREEZE: BLOCKED — missing-verdict` (a failed pass: do not freeze, re-run), never implicit
agreement. The propose workflow SHALL gate the freeze on `freeze_check.py` and route each `BLOCKED`
reason to its handler — `needs-revision` to the mandatory-re-review path, `premise-dissent` to the
operator `AskUserQuestion` (re-frame / re-scope / override), and `missing-verdict` to a review re-run.
The orchestrator MAY overrule a demonstrably-false `BLOCKED` only by recording the rationale in
`review-log.md` (the existing "reviewer can be wrong" authority). `design.md` and `tasks.md` SHALL
retain the zero-🔴 freeze rule, likewise determined by `freeze_check.py` from the `VERDICT` token (no
`PREMISE` required for those artifacts).

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

#### Scenario: Bolded verdict and premise tokens parse identically to unbolded ones
- **WHEN** a review's whole-line token carries optional `**` markdown emphasis around the label, the
  value, or both — e.g. `**VERDICT:** PASS`, `**VERDICT: PASS**`, `**PREMISE: AGREE**`
- **THEN** `freeze_check.py` SHALL parse each identically to its unbolded form (`VERDICT: PASS`,
  `PREMISE: AGREE`) and derive the same freeze verdict

#### Scenario: A verdict token quoted mid-prose is not accepted
- **WHEN** review text contains a `VERDICT: PASS`-shaped or `PREMISE: AGREE`-shaped token embedded inside
  a prose sentence rather than alone on its own line
- **THEN** `freeze_check.py` SHALL NOT treat it as a parsed verdict, and SHALL fail closed to
  `FREEZE: BLOCKED — missing-verdict` when no valid whole-line token is otherwise present

### Requirement: A premise dissent is surfaced to the operator and never silently auto-resolved
A premise dissent SHALL be surfaced to the operator and never silently auto-resolved, because it is a
direction fault rather than an auto-fixable artifact defect. When a `proposal.md` review returns
`PREMISE: DISSENT`, the propose workflow SHALL stop the freeze loop and present the cited concerns to the
operator via `AskUserQuestion` with three options — re-frame, re-scope, or override-to-proceed — and
record the operator's choice and rationale in `review-log.md`. Only
override-to-proceed permits freezing on a dissent; after override, the freeze condition reverts to zero
🔴 only and the dissent is not re-litigated on re-review.

#### Scenario: Operator chooses to revise
- **WHEN** the operator responds to a surfaced dissent by selecting re-frame or re-scope
- **THEN** the proposal is revised and re-reviewed, and does not freeze on the dissent

#### Scenario: Operator overrides
- **WHEN** the operator selects override-to-proceed with a recorded rationale
- **THEN** the proposal may freeze once it has zero 🔴, and the dissent is not re-raised on re-review

### Requirement: The SMALL premise pass runs before apply, independent of operator confirmation, and is gated at apply
For a SMALL change the orchestrator SHALL run the premise pass after the plan is written and **before
apply delegation** — a trigger independent of operator confirmation, so it fires identically with or
without an autonomy grant. The orchestrator SHALL extract the verdict from the reviewer's stdout (the
reviewer is `edit: deny`) and write only the verdict block to `premise-review.md` in the plan's
directory. On timeout or crash the orchestrator SHALL apply the same salvage rules as the propose reviewer
(extract partial output; re-run once if more than 120s elapsed or any finding is present; else escalate),
writing the partial to `premise-review.md` marked `PARTIAL`. Without an autonomy
grant the verdict SHALL be presented inside the operator's tier+plan confirmation. Under an autonomy grant
the grant covers tier self-classification only and SHALL NOT override a premise dissent: a `DISSENT` with
no recorded operator override SHALL leave the apply gate stopped and the orchestrator SHALL escalate to
the operator. The apply workflow SHALL, for a SMALL change, after change selection and before
implementation delegation, assert `premise-review.md` exists with a resolved verdict (`AGREE` or a
recorded override-to-proceed) and SHALL STOP otherwise. The apply workflow SHALL NOT itself invoke the
premise reviewer. A SMALL plan SHALL contain at minimum a problem statement, a proposed approach, and an
explicit out-of-scope note for the premise reviewer to assess; a structurally inadequate plan is reported
as a finding rather than guessed at.

#### Scenario: SMALL premise pass fires under autonomy
- **WHEN** a SMALL change is processed under an autonomy grant (no operator confirmation prompt exists)
- **THEN** the orchestrator still runs the premise pass before apply and writes the verdict to `premise-review.md`

#### Scenario: Autonomy does not override a dissent
- **WHEN** a SMALL premise pass returns `DISSENT` under an autonomy grant with no recorded operator override
- **THEN** the apply gate STOPs and the orchestrator escalates to the operator rather than proceeding

#### Scenario: Apply gate blocks an unresolved SMALL premise verdict
- **WHEN** the apply workflow processes a SMALL change whose `premise-review.md` is missing or unresolved
- **THEN** it STOPs before delegating implementation

#### Scenario: Apply gate passes a resolved SMALL premise verdict
- **WHEN** the apply workflow processes a SMALL change whose `premise-review.md` records `AGREE` or a recorded override-to-proceed
- **THEN** it proceeds to delegate implementation

#### Scenario: SMALL premise pass timeout is salvaged to premise-review.md
- **WHEN** the SMALL flash premise pass times out or crashes
- **THEN** the orchestrator salvages partial output per the reviewer-budget salvage rules and writes it to `premise-review.md` marked `PARTIAL` (not to `review-log.md`, which the SMALL flow lacks)
- **AND** the written output is marked `PARTIAL`

#### Scenario: Reviewer flags a structurally inadequate SMALL plan
- **WHEN** a SMALL plan lacks a problem statement, a proposed approach, or an explicit out-of-scope note
- **THEN** the premise reviewer reports the missing structure as a finding rather than guessing at the absent content

### Requirement: The explore skill owns and runs the direction gate on an advancement signal
The explore skill SHALL run the direction gate itself — it invokes `openspec-reviewer` via `opencode run`
using the existing delegation harness (the same pattern the propose skill uses), and reports the verdict to
the operator before the phase advances. The gate SHALL fire only when the operator makes an **explicit
advancement choice** (the skill offers it when exploration crystallizes; the operator may also invoke it
directly) — not by keyword-sniffing free text — so the explore skill's "no mandatory output" principle is
preserved for idle exploration. On firing, the skill SHALL write `explore-brief.md`, run the
`deepseek/deepseek-v4-pro` review under the standard 780s / `-k 15` envelope and salvage rules, and SHALL
NOT advance the phase until the verdict is resolved.

#### Scenario: Idle exploration triggers nothing
- **WHEN** the operator explores ideas without choosing to advance
- **THEN** no `explore-brief.md` is written and no direction review runs

#### Scenario: Advancement choice fires the gate
- **WHEN** the operator makes the explicit advancement choice (or asks to gate the brief)
- **THEN** the explore skill writes `explore-brief.md`, runs the pro direction review, and does not surface the propose/apply hint until the verdict is resolved

### Requirement: The explore brief and its verdict have a defined home, slug, and relocation
The explore skill SHALL write the brief and its review output to a `plans/<slug>/` directory —
`plans/<slug>/explore-brief.md` and `plans/<slug>/premise-review.md` — created with `mkdir -p` on first
write, where `<slug>` is a kebab-case identifier derived from the exploration topic (the same convention the
propose skill uses to derive a change name), disambiguated on collision. The orchestrator SHALL extract the
verdict block from the reviewer's stdout (the reviewer is `edit: deny`) into `premise-review.md`. When the
operator advances to `propose`, the propose skill SHALL relocate `explore-brief.md` and `premise-review.md`
into the change directory so all of a change's artifacts share one canonical location; it SHALL best-effort
skip relocation when no matching `plans/` directory is found. For a SMALL change (no propose) the brief and
verdict remain in `plans/<slug>/`.

#### Scenario: Brief written to plans with a derived slug
- **WHEN** the explore direction gate fires for an exploration topic
- **THEN** `plans/<slug>/explore-brief.md` and `plans/<slug>/premise-review.md` are written with `<slug>` derived kebab-case from the topic

#### Scenario: Propose relocates the brief into the change dir
- **WHEN** the operator advances a verified brief to `propose` and the change directory is created
- **THEN** the propose skill moves `explore-brief.md` and `premise-review.md` from `plans/<slug>/` into the change directory
- **AND** the propose skill learns `<slug>` from the explore skill's advancement hint so it can locate `plans/<slug>/`

### Requirement: A direction dissent at explore is surfaced and its override propagates
A `PREMISE: DISSENT` at the explore altitude SHALL be surfaced to the operator via the same three-way
decision as the proposal path — re-think direction / re-scope / override-to-proceed. The verdict block in
`premise-review.md` SHALL be machine-parseable: an override SHALL be recorded as a `### Resolution` section
containing a single `OVERRIDE: proceed — <rationale>` line beneath the `### Premise Verdict` block. Any later
review that receives a verified brief as context (the SMALL plan pass or the MEDIUM/COMPLEX proposal review)
SHALL treat direction as **settled** when `premise-review.md` contains either `PREMISE: AGREE` or
`OVERRIDE: proceed`, and SHALL NOT re-raise the settled dissent as a fresh one.

#### Scenario: Override is recorded machine-parseably and propagates
- **WHEN** the operator overrides a `PREMISE: DISSENT` at explore to proceed
- **THEN** an `OVERRIDE: proceed — <rationale>` line is recorded in `premise-review.md` and the later drift check treats the direction as settled rather than re-raising the dissent

#### Scenario: Re-think loops back without an override marker
- **WHEN** the operator chooses re-think or re-scope on an explore dissent
- **THEN** no `OVERRIDE` line is written and the brief is revised and re-reviewed

### Requirement: Drift from a verified brief is concretely defined and flagged as a dissent
When a verified `explore-brief.md` is handed to a later review as context, the reviewer SHALL be instructed
to also flag **drift**, defined as the later artifact (a) reframing the problem differently from the brief's
verified problem, (b) changing to an approach the brief explicitly ruled out, or (c) expanding scope beyond
what was vetted at explore. Narrower scope, restatements, and added implementation detail SHALL NOT be
treated as drift. Drift SHALL surface as a normal `PREMISE: DISSENT`.

#### Scenario: Scope expansion beyond the vetted direction is drift
- **WHEN** a proposal or plan expands scope beyond what the verified brief vetted
- **THEN** the reviewer flags it as drift via `PREMISE: DISSENT`

#### Scenario: A narrower plan is not drift
- **WHEN** a plan is more conservative than the verified brief (narrower scope, restated problem)
- **THEN** the reviewer does not treat it as drift

### Requirement: The explore-altitude review is calibrated for an abstract brief
At the explore altitude the reviewer SHALL dissent only when the direction is **demonstrably wrong given the
information available** (a symptom mistaken for the root, a solution that cannot address the stated problem,
or an approach ruled out by evidence) — and SHALL NOT dissent merely because the brief is under-specified,
which is expected at the explore stage and is at most a 🟡/💡 note. Where the brief's scope is not yet
concrete, the reviewer SHALL note "scope not yet concrete — deferred to proposal" rather than treat it as a
fault.

#### Scenario: Under-specification is not a dissent
- **WHEN** an explore brief is thin on concrete scope but its direction is sound
- **THEN** the reviewer emits `PREMISE: AGREE` (noting scope is deferred to proposal), not `PREMISE: DISSENT`

#### Scenario: A demonstrably wrong direction is a dissent
- **WHEN** an explore brief mistakes a symptom for the root cause
- **THEN** the reviewer emits `PREMISE: DISSENT` with the cited root-cause concern
