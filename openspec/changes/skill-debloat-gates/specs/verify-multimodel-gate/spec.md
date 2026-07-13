# Delta — verify-multimodel-gate (mechanized-verify-propose-gates)

The two COMPLEX verifier passes (pro behavioral + flash lens) are independent, read-only reviews of
an already-frozen tree, but the skill prose currently launches them sequentially (pro fully resolves,
including any fix/re-run, before lens starts) — costing ~13 min of avoidable wall-clock. This delta
clarifies that the two COMPLEX passes MAY be launched concurrently, while leaving the hard-gate and
rerun-failed-and-after recovery semantics exactly as they are.

## MODIFIED Requirements

### Requirement: Each verification pass is a hard gate with rerun-failed-and-after recovery
Each pass SHALL be a hard gate: verify does not complete until every pass in the tier's sequence returns READY. For a COMPLEX change the two verifier passes (the `deepseek/deepseek-v4-pro` behavioral pass and the `deepseek/deepseek-v4-flash` lens pass) MAY be launched concurrently on the frozen tree — they are independent, read-only, and do not depend on each other's output — with the orchestrator waiting for both completion sentinels before judging; concurrency is an initial-launch optimization only and does NOT change the gate or recovery semantics below. When a pass returns NEEDS REVISION and the orchestrator confirms the defect from disk, the orchestrator SHALL fix it via the existing defect re-delegation path (re-delegate to the apply-executor, one attempt, escalate to a Sonnet subagent on operational or quality failure), then SHALL re-run the pass that failed and every pass after it in sequence — never the passes before it — serializing that fix→re-run cycle. If the same pass returns NEEDS REVISION across three fix cycles without clearing, the orchestrator SHALL stop and escalate to the operator with the accumulated verdicts.

#### Scenario: The COMPLEX passes are launched concurrently then judged
- **WHEN** a COMPLEX change reaches the multi-model passes on a frozen tree
- **THEN** the orchestrator MAY launch the pro behavioral pass and the flash lens pass concurrently and wait for both completion sentinels before judging either
- **AND** if both return READY, verify proceeds with no re-run

#### Scenario: The last pass fails and is fixed
- **WHEN** the lens pass (last in the COMPLEX sequence) or the pro pass (last in the MEDIUM sequence) returns NEEDS REVISION with a confirmed defect
- **THEN** the orchestrator fixes the defect via re-delegation and re-runs only that pass

#### Scenario: An earlier pass fails and reruns the rest
- **WHEN** the pro pass returns NEEDS REVISION with a confirmed defect on a COMPLEX change
- **THEN** the orchestrator fixes it and re-runs the pro pass and then the lens pass, but not the self-review

#### Scenario: Non-convergence after three cycles escalates
- **WHEN** the same pass returns NEEDS REVISION on three successive fix cycles
- **THEN** the orchestrator stops and escalates to the operator with the accumulated verdicts rather than looping further
