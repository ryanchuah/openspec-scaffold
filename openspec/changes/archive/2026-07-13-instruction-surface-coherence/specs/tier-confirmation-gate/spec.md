# Delta — tier-confirmation-gate (instruction-surface-coherence)

Additive delta resolving the autonomy-grant-vs-phase-gate contradiction (OW-9). The existing
capability governs the **tier** confirmation checkpoint (no grant → confirm before executing;
grant → self-classify). The four lifecycle skills separately assert an unconditional phase-gate
STOP ("never advance without an explicit user request — hard rule") with no autonomy carve-out —
so an autonomy-granted orchestrator receives contradictory instructions at every phase boundary.
This delta adds the missing requirement: it names exactly what an autonomy grant does and does NOT
authorize at a phase boundary, giving the skills one spec requirement to cite instead of each
restating an unconditional STOP. Permission-posture and tier requirements are untouched.

## ADDED Requirements

### Requirement: An autonomy grant auto-advances lifecycle phases except across a dissent, a revision escalation, or an operator-named gate
Under an explicit autonomy grant, an orchestrator SHALL be permitted to advance from one OpenSpec lifecycle phase to the next (propose → apply → verify → archive) without a fresh per-phase operator request, EXCEPT it SHALL halt and surface to the operator across three boundaries: (a) a premise **DISSENT**, (b) a verify **NEEDS-REVISION** escalation that the verify skill's own defect loop cannot clear, or (c) any **operator-named gate** (downstream propagation, push-to-remote, or any boundary the operator explicitly reserved).
Without an autonomy grant, every phase boundary SHALL remain a hard STOP requiring an explicit
operator request before the next phase begins. This requirement is the single canonical source of
the phase-advance rule; the lifecycle skills' phase-gate sections cite it rather than each asserting
an independent unconditional STOP.

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
