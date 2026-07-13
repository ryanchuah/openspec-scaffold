## Purpose

Require an agent without an autonomy grant to confirm the proposed change tier and plan with the operator before executing, preventing autonomous self-classification from bypassing the operator checkpoint.

## Requirements

### Requirement: An agent without an autonomy grant confirms the change tier before executing
An agent operating WITHOUT an explicit autonomy grant SHALL NOT self-assign a change tier
(SMALL / MEDIUM / COMPLEX) and begin executing it. It SHALL first state its proposed tier together
with a plan, and SHALL obtain explicit operator confirmation before beginning execution — delegating
the apply phase, editing implementation code, or otherwise mutating project code/state. Producing the
plan itself (a proposal or a written tier recommendation) is how the agent surfaces the choice and is
NOT gated — the gate sits between planning and execution, not before planning. An agent WITH an
explicit autonomy grant SHALL self-classify and proceed under that grant (autonomy is operator-told and ephemeral — there is no autonomy doc or mode, by design).
Change tiering itself remains standing (it applies regardless of any autonomy grant); only the requirement to
*confirm before executing* is gated on the absence of a grant.

#### Scenario: No autonomy grant — propose and wait
- **WHEN** an agent without an autonomy grant has classified a change's tier
- **THEN** it states the proposed tier and plan to the operator and waits for confirmation
- **AND** it does NOT begin execution (no apply delegation, no code edits, no archive) until the operator confirms

#### Scenario: Operator confirms the tier
- **WHEN** the operator confirms the proposed tier or selects a different one
- **THEN** the agent proceeds at the confirmed tier

#### Scenario: Autonomy granted — self-classify
- **WHEN** an agent has an explicit autonomy grant for the session or task
- **THEN** it may self-classify the tier and proceed without per-change confirmation, under that grant

#### Scenario: Operator unavailable
- **WHEN** an agent without an autonomy grant cannot obtain operator confirmation (the operator is away)
- **THEN** the tier remains unconfirmed and the agent does NOT execute — it reports the proposed tier and plan and waits, rather than defaulting to autonomous execution

### Requirement: An autonomy grant auto-advances lifecycle phases except across a dissent, a revision escalation, or an operator-named gate
Under an explicit autonomy grant, an orchestrator SHALL be permitted to advance from one OpenSpec lifecycle phase to the next (propose → apply → verify → archive) without a fresh per-phase operator request, EXCEPT it SHALL halt and surface to the operator across three boundaries: (a) a premise **DISSENT**, (b) a verify **NEEDS-REVISION** escalation that the verify skill's own defect loop cannot clear, or (c) any **operator-named gate** (downstream propagation, push-to-remote, or any boundary the operator explicitly reserved).
Without an autonomy grant, every phase boundary SHALL remain a hard STOP requiring an explicit operator request before the next phase begins. This requirement is the single canonical source of the phase-advance rule; the lifecycle skills' phase-gate sections cite it rather than each asserting an independent unconditional STOP.

#### Scenario: Autonomy grant — clean phase auto-advances
- **WHEN** an orchestrator holds an explicit autonomy grant and a lifecycle phase completes with no premise DISSENT, no unresolved verify NEEDS-REVISION, and no pending operator-named gate
- **THEN** it proceeds to the next phase without requesting fresh per-phase confirmation

#### Scenario: Autonomy grant — halt on premise dissent
- **WHEN** a premise review returns `PREMISE: DISSENT`
- **THEN** the orchestrator halts and surfaces the dissent to the operator, regardless of any autonomy grant, and does NOT auto-advance until the operator re-frames, re-scopes, or overrides

#### Scenario: Autonomy grant — halt at an operator-named gate
- **WHEN** the next action under an autonomy grant is a downstream propagation or a push-to-remote (or another boundary the operator explicitly reserved)
- **THEN** the orchestrator halts for explicit operator authorization even though the grant is in force

#### Scenario: No autonomy grant — every phase boundary is a hard stop
- **WHEN** an orchestrator without an autonomy grant completes a lifecycle phase
- **THEN** it stops at the phase boundary and requests explicit operator confirmation before beginning the next phase
