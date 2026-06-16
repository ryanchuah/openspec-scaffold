## Purpose

Require independent multi-model verification passes as hard gates in the verify step, so a release decision is never gated on a single model's blind spots. This capability defines the platform-specific pass chain, the hard-gate / rerun-failed-and-after recovery semantics, the read-only delegated verifier agent contract, and the audit trail of per-pass verdicts.

## ADDED Requirements

### Requirement: Verify runs independent multi-model passes after the self-review
The verify step SHALL run independent verification passes by additional models, layered immediately after the orchestrator's MANDATORY behavioral review (the self-review, "pass 1") and before the artifact/spec mapping checklist and the report/`notes.md` steps. The self-review remains the orchestrator's own non-delegated review; the additional passes SHALL NOT replace it. The pass sequence SHALL depend on the orchestrator's platform: a Claude Code orchestrator SHALL run self-review → a `deepseek/deepseek-v4-pro` verifier pass → a `deepseek/deepseek-v4-flash` verifier pass; an OpenCode orchestrator SHALL run self-review → a `deepseek/deepseek-v4-flash` verifier pass only.

#### Scenario: Claude Code orchestrator runs three passes
- **WHEN** the orchestrator is Claude Code and the self-review completes
- **THEN** a `deepseek/deepseek-v4-pro` verifier pass runs, then a `deepseek/deepseek-v4-flash` verifier pass runs, before any report or `notes.md` is written

#### Scenario: OpenCode orchestrator runs the flash pass only
- **WHEN** the orchestrator is OpenCode and the self-review completes
- **THEN** a single `deepseek/deepseek-v4-flash` verifier pass runs, and no pro pass runs

#### Scenario: The self-review is preserved
- **WHEN** the multi-model passes run
- **THEN** the orchestrator has already performed its own non-delegated behavioral review, and the delegated passes are additional confirmations rather than a substitute for it

### Requirement: Each verification pass is a hard gate with rerun-failed-and-after recovery
Each pass SHALL be a hard gate: verify does not complete until every pass in the platform's sequence returns READY. When a pass returns NEEDS REVISION and the orchestrator confirms the defect from disk, the orchestrator SHALL fix it via the existing defect re-delegation path (re-delegate to the apply-executor, one attempt, escalate to a Sonnet subagent on operational or quality failure), then SHALL re-run the pass that failed and every pass after it in sequence — never the passes before it. If the same pass returns NEEDS REVISION across three fix cycles without clearing, the orchestrator SHALL stop and escalate to the operator with the accumulated verdicts.

#### Scenario: A later pass fails and is fixed
- **WHEN** the flash pass (last in the Claude sequence) returns NEEDS REVISION with a confirmed defect
- **THEN** the orchestrator fixes the defect via re-delegation and re-runs only the flash pass

#### Scenario: An earlier pass fails and reruns the rest
- **WHEN** the pro pass returns NEEDS REVISION with a confirmed defect
- **THEN** the orchestrator fixes it and re-runs the pro pass and then the flash pass, but not the self-review

#### Scenario: Non-convergence after three cycles escalates
- **WHEN** the same pass returns NEEDS REVISION on three successive fix cycles
- **THEN** the orchestrator stops and escalates to the operator with the accumulated verdicts rather than looping further

### Requirement: The delegated verifier runs the behavioral review read-only and emits a machine-discriminable verdict
The delegated verifier SHALL perform the same behavioral review the self-review performs — read the `git diff` and changed files, re-run the full test suite via the per-repo command (`scripts/test-cmd` or the project's documented command, never an improvised command), eyeball a concrete sample of real output, and for an external-API surface run the live smoke (a skipped smoke is not a pass; a missing smoke on an external-API change is itself a critical defect). The verifier SHALL NOT modify files; fixing defects is the orchestrator's responsibility. The verifier SHALL emit a verdict block beginning with a `## Verify Pass — <model>` heading and a `VERDICT: READY` or `VERDICT: NEEDS REVISION` line, followed by a `### Defects` section that is always present (containing `- None` when there are no defects, otherwise file:line-cited defect entries).

#### Scenario: Verifier reports a defect without fixing it
- **WHEN** the verifier finds a defect during its behavioral review
- **THEN** it emits `VERDICT: NEEDS REVISION` with a file:line-cited defect entry and makes no file edits

#### Scenario: Verifier passes cleanly
- **WHEN** the verifier's behavioral review finds no defect
- **THEN** it emits `VERDICT: READY` and a `### Defects` section containing `- None`

### Requirement: The orchestrator asserts the real verifier ran and judges findings from disk
Before trusting any pass output, the orchestrator SHALL assert the real verifier ran: it SHALL treat a `Falling back to default agent` warning on the invocation's stderr as a failure (do not use the output; escalate), and SHALL confirm the extracted output contains a `## Verify Pass` heading and a `VERDICT:` line. The orchestrator SHALL judge every reported finding from disk (`git diff`, re-run) rather than accept it on the verifier's word, and MAY overrule a demonstrably false finding only by recording the rationale in the review/`notes.md`.

#### Scenario: Silent fallback is rejected
- **WHEN** the verifier invocation's stderr contains `Falling back to default agent`
- **THEN** the orchestrator does not use the output and escalates

#### Scenario: A finding is confirmed from disk before fixing
- **WHEN** a verifier reports a defect
- **THEN** the orchestrator reproduces or confirms it from disk before initiating a fix, and records a rationale if it overrules the finding as false

### Requirement: A single verifier agent serves both models
The verifier SHALL be defined by a single agent file `.opencode/agents/openspec-verifier.md` with default `model: deepseek/deepseek-v4-flash`. The OpenCode path SHALL invoke it via the Task tool (`subagent_type: openspec-verifier`) at its default model. The Claude Code path SHALL invoke it via `opencode run --agent openspec-verifier` and select the model per pass with `--model` (`deepseek/deepseek-v4-pro`, then `deepseek/deepseek-v4-flash`), overriding the frontmatter default.

#### Scenario: Claude Code selects the model per pass
- **WHEN** the Claude Code orchestrator runs the pro pass then the flash pass
- **THEN** each invocation passes the corresponding `--model`, overriding the agent's frontmatter default

#### Scenario: OpenCode uses the frontmatter default
- **WHEN** the OpenCode orchestrator spawns `subagent_type: openspec-verifier`
- **THEN** the pass runs on the frontmatter default `deepseek/deepseek-v4-flash` with no model override

### Requirement: Each pass's verdict and model are recorded
The verification report and `notes.md` SHALL record, for each pass in the platform's sequence, the model that ran it, its verdict, and any defect it caught (attributed to the pass that surfaced it).

#### Scenario: The report attributes defects to passes
- **WHEN** the verification report and `notes.md` are written after all passes clear
- **THEN** they list each pass (self / pro / flash), its model and verdict, and which pass surfaced each defect that was found and fixed

#### Scenario: A re-run pass records both verdicts
- **WHEN** a pass returns NEEDS REVISION, the defect is fixed, and the pass is re-run to READY
- **THEN** the report and `notes.md` record both the original NEEDS REVISION and the final READY verdict for that pass
