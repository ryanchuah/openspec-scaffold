## MODIFIED Requirements

### Requirement: Recovery from a declared blocker is the orchestrator's decision
On a declared non-convergence blocker the primary SHALL choose recovery by triage rather than
reflexively escalating to Sonnet, on BOTH delegation paths. Triage options SHALL include: tighten
the brief / re-slice and dispatch a fresh executor (brief/plan gap); escalate to the user
(artifact/decision gap); or spawn a Sonnet subagent (model-capability gap). This recovery routing
SHALL hold in ALL autonomy modes: a fast-track/autonomy grant relaxes interactive checkpointing but
SHALL NOT replace declared-blocker triage with an unconditional "non-crash failure → Sonnet
immediately" ladder.

#### Scenario: Claude delegation path
- **WHEN** the Claude-Code primary receives a declared blocker
- **THEN** it selects a triage branch (fresh executor / escalate / Sonnet) instead of auto-Sonnet

#### Scenario: OpenCode delegation path
- **WHEN** the OpenCode primary receives a declared blocker
- **THEN** it reports the blocker with the triage options to the user rather than silently waiting

#### Scenario: Recovery routing holds under fast-track / autonomy
- **WHEN** the primary is operating under a fast-track/autonomy grant and receives a declared blocker
- **THEN** it still selects a triage branch and does NOT reflexively escalate to Sonnet
- **AND** the fast-track guidance does NOT state an unconditional "non-crash failure → Sonnet immediately" ladder
