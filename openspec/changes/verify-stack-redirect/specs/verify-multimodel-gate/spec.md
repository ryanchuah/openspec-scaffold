# Delta — verify-multimodel-gate (verify-stack-redirect)

## MODIFIED Requirements

### Requirement: Verify runs independent multi-model passes after the self-review
The verify step SHALL run independent verification passes by additional models, layered immediately after the orchestrator's MANDATORY behavioral review (the self-review, "pass 1") and before the artifact/spec mapping checklist and the report/`notes.md` steps. The self-review remains the orchestrator's own non-delegated review; the additional passes SHALL NOT replace it. These passes apply to **MEDIUM and COMPLEX** changes ONLY: a SMALL change does its own verification per `AGENTS.md` — including its REQUIRED single `deepseek/deepseek-v4-flash` verifier pass, run outside the verify skill — and SHALL NOT run these passes or invoke the verify skill. The pass sequence SHALL be identical on both orchestrator platforms (Claude Code and OpenCode) and SHALL depend on tier: for a **MEDIUM** change, self-review → one `deepseek/deepseek-v4-pro` behavioral verifier pass; for a **COMPLEX** change, self-review → one `deepseek/deepseek-v4-pro` behavioral verifier pass → one `deepseek/deepseek-v4-flash` **lens** verifier pass (see the lens-pass requirement). No pass in the sequence SHALL be a third run of the same behavioral checklist: the recorded three-repo history showed zero non-trivial defects uniquely caught by a same-checklist third pass, so same-lens breadth beyond self + one model is deliberately not purchased.

#### Scenario: A MEDIUM change runs two passes
- **WHEN** the change is MEDIUM and the self-review completes
- **THEN** a `deepseek/deepseek-v4-pro` behavioral verifier pass runs, before any report or `notes.md` is written
- **AND** no same-checklist third pass follows it

#### Scenario: A COMPLEX change runs three passes with a lens-diverse third
- **WHEN** the change is COMPLEX and the self-review completes
- **THEN** a `deepseek/deepseek-v4-pro` behavioral verifier pass runs, then a `deepseek/deepseek-v4-flash` lens verifier pass runs, before any report or `notes.md` is written

#### Scenario: The sequence is identical on both platforms
- **WHEN** the orchestrator is Claude Code or OpenCode and the change is MEDIUM or COMPLEX
- **THEN** the tier's pass sequence is the same on either platform

#### Scenario: A SMALL change runs self-review plus a required flash pass
- **WHEN** the change is SMALL
- **THEN** it does NOT invoke the verify skill, its multi-model passes, or the verify phase-gate STOP
- **AND** the orchestrator SHALL run a single `deepseek/deepseek-v4-flash` verifier pass (same invocation shape as the verify skill's behavioral pass, outside the verify skill)

#### Scenario: The self-review is preserved
- **WHEN** the multi-model passes run (for MEDIUM/COMPLEX)
- **THEN** the orchestrator has already performed its own non-delegated behavioral review, and the delegated passes are additional confirmations rather than a substitute for it

### Requirement: Each verification pass is a hard gate with rerun-failed-and-after recovery
Each pass SHALL be a hard gate: verify does not complete until every pass in the tier's sequence returns READY. When a pass returns NEEDS REVISION and the orchestrator confirms the defect from disk, the orchestrator SHALL fix it via the existing defect re-delegation path (re-delegate to the apply-executor, one attempt, escalate to a Sonnet subagent on operational or quality failure), then SHALL re-run the pass that failed and every pass after it in sequence — never the passes before it. If the same pass returns NEEDS REVISION across three fix cycles without clearing, the orchestrator SHALL stop and escalate to the operator with the accumulated verdicts.

#### Scenario: The last pass fails and is fixed
- **WHEN** the lens pass (last in the COMPLEX sequence) or the pro pass (last in the MEDIUM sequence) returns NEEDS REVISION with a confirmed defect
- **THEN** the orchestrator fixes the defect via re-delegation and re-runs only that pass

#### Scenario: An earlier pass fails and reruns the rest
- **WHEN** the pro pass returns NEEDS REVISION with a confirmed defect on a COMPLEX change
- **THEN** the orchestrator fixes it and re-runs the pro pass and then the lens pass, but not the self-review

#### Scenario: Non-convergence after three cycles escalates
- **WHEN** the same pass returns NEEDS REVISION on three successive fix cycles
- **THEN** the orchestrator stops and escalates to the operator with the accumulated verdicts rather than looping further

### Requirement: The delegated verifier runs the behavioral review read-only and emits a machine-discriminable verdict
The delegated verifier SHALL execute the fixed review prompt supplied by its invocation. For a **behavioral pass** (the default when the prompt specifies no lens), it SHALL perform the same behavioral review the self-review performs — read the `git diff` and changed files, re-run the full test suite via the per-repo command (`scripts/test-cmd` or the project's documented command, never an improvised command), eyeball a concrete sample of real output, and for an external-API surface run the live smoke (a skipped smoke is not a pass; a missing smoke on an external-API change is itself a critical defect). For a **lens pass**, it SHALL execute the lens prompt's checklist instead (see the lens-pass requirement). In all cases the verifier SHALL NOT modify files; fixing defects is the orchestrator's responsibility. The verifier SHALL emit a verdict block beginning with a `## Verify Pass — <model>` heading and a `VERDICT: READY` or `VERDICT: NEEDS REVISION` line, followed by a `### Defects` section that is always present (containing `- None` when there are no defects, otherwise file:line-cited defect entries).

#### Scenario: Verifier reports a defect without fixing it
- **WHEN** the verifier finds a defect during its review (behavioral or lens)
- **THEN** it emits `VERDICT: NEEDS REVISION` with a file:line-cited defect entry and makes no file edits

#### Scenario: Verifier passes cleanly
- **WHEN** the verifier's review finds no defect
- **THEN** it emits `VERDICT: READY` and a `### Defects` section containing `- None`

#### Scenario: The lens pass shares the verdict contract
- **WHEN** the lens pass completes
- **THEN** its output uses the identical `## Verify Pass` / `VERDICT:` / `### Defects` block, so the orchestrator's gate mechanics need no per-lens handling

### Requirement: A single verifier agent serves both models, invoked via opencode run on both platforms
The verifier SHALL be defined by a single agent file `.opencode/agents/openspec-verifier.md` with default `model: deepseek/deepseek-v4-flash`. The same agent file SHALL serve both the behavioral and lens passes — the invocation's fixed prompt is the parameterization point; no second agent file is introduced (which would add a new permission surface and dangling-reference risk). Both platforms SHALL invoke it via `opencode run --agent openspec-verifier` with a `--model` flag per pass (`deepseek/deepseek-v4-pro` for the behavioral pass; `deepseek/deepseek-v4-flash` for the lens pass), overriding the frontmatter default. All invocations apply the full delegation harness (`< /dev/null`, `--dir`, EXIT-sentinel, bounded wait) per `.claude/skills/_shared/delegation-harness.md`.

#### Scenario: Both platforms select the model per pass
- **WHEN** either a Claude Code or an OpenCode orchestrator runs the behavioral pass (and, on COMPLEX, the lens pass)
- **THEN** each invocation passes the corresponding `--model` via `opencode run`, overriding the agent's frontmatter default

#### Scenario: One agent file, two prompts
- **WHEN** the behavioral pass and the lens pass run
- **THEN** both load the same `openspec-verifier` agent definition (same read-only posture and permissions), differing only in the fixed prompt and `--model`

### Requirement: Each pass's verdict and model are recorded
The verification report and `notes.md` SHALL record, for each pass in the tier's sequence, the model that ran it, its verdict, for a lens pass which lens was selected (with the orchestrator's one-line selection rationale), and any defect it caught — attributed to the pass that surfaced it (self-review, pro pass, or lens pass).

#### Scenario: The report attributes defects to passes
- **WHEN** the verification report and `notes.md` are written after all passes clear
- **THEN** they list each pass (self / pro / lens), its model, verdict, and — for the lens pass — the selected lens and rationale, and which pass surfaced each defect that was found and fixed

#### Scenario: A re-run pass records both verdicts
- **WHEN** a pass returns NEEDS REVISION, the defect is fixed, and the pass is re-run to READY
- **THEN** the report and `notes.md` record both the original NEEDS REVISION and the final READY verdict for that pass

## ADDED Requirements

### Requirement: The COMPLEX third pass runs a lens the behavioral stack lacks
For a COMPLEX change, the third delegated pass SHALL be a **lens pass**: a fixed prompt asking questions the behavioral checklist does not ask, rather than a third run of the same behavioral checklist. The verify skill SHALL carry the canonical lens prompts inline (not by pointer into an archived change). The v1 lens menu is:
- **Test-quality / adversarial-oracle lens (default):** for each test the change adds or modifies, would the test fail if the behavior it claims to cover broke — name the assertion that would trip; flag tautological or forced-green assertions, empty test bodies, mocks that replace the module under test, discarded return values/flags, and unfrozen clocks in tests.
- **Data-scale lens (for data-path-dominant changes):** which input domains are unbounded in production; whether the change fully materializes an unbounded query result (e.g. `fetchall()` on an unbounded query); whether the change needs an at-scale run or a recorded bounded-domain argument.

The orchestrator SHALL select the lens per change and record the selection with a one-line rationale in `review-log.md`. The lens pass is **diff-scoped**: it SHALL NOT be required to re-run the full test suite (the pro behavioral pass has already done so) and MAY run targeted commands/probes instead. Its findings are leads the orchestrator confirms from disk, and it retains the hard-gate and recovery semantics of the pass-sequence requirements. The orchestrator MAY additionally run a lens pass on a MEDIUM change when the change's risk profile warrants it, under the same contract and recording rules. A prompt-based lens is a stepping stone with lower precision than a deterministic detector; when a corresponding detector ships (e.g. a test-quality or data-scale check), the lens prompt SHALL direct the verifier to run and confirm the detector's findings rather than rediscover them.

#### Scenario: Default lens selection
- **WHEN** a COMPLEX change has no dominant data-path risk
- **THEN** the orchestrator selects the test-quality/adversarial-oracle lens and records the selection with a one-line rationale in `review-log.md`

#### Scenario: Data-scale lens for a data-path change
- **WHEN** a COMPLEX change's dominant risk is data-path behavior (unbounded inputs, query volume, large-scale processing)
- **THEN** the orchestrator selects the data-scale lens and records the selection with a one-line rationale in `review-log.md`

#### Scenario: The lens pass does not re-run the full suite
- **WHEN** the lens pass runs
- **THEN** it is not required to re-run the full test suite and may run targeted probes scoped to its lens questions

#### Scenario: The lens pass is a hard gate
- **WHEN** the lens pass returns NEEDS REVISION and the orchestrator confirms the defect from disk
- **THEN** the existing fix → re-run-failed-pass recovery path applies, including the three-cycle escalation bound

#### Scenario: A MEDIUM change opts into a lens pass
- **WHEN** the orchestrator judges a MEDIUM change's risk profile to warrant a lens pass
- **THEN** it MAY run one flash lens pass after the pro pass, with the same selection recording, gate semantics, and verdict contract
