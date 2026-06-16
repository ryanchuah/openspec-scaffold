## Purpose

Stop the apply-executor from looping on a stuck failure by giving it an objective, deterministic non-convergence stop condition, and route a diagnosed blocker to orchestrator triage instead of reflexive escalation.

## Requirements

### Requirement: The apply-executor stops on non-convergence
The apply-executor SHALL continue healthy `write → test → fix` iteration, but SHALL stop editing and
report a blocker when it detects non-convergence, defined as ANY of: (a) the same failing test still
fails with the same normalized error signature after 2 consecutive fix attempts aimed at it; (b) it
is about to edit the same file a 3rd time to resolve the same failure; (c) the fix requires
information or a decision absent from the artifacts, requires editing `proposal.md`/`design.md`, or
an external API behaves contrary to `design.md`. For its test runs the executor SHALL prefer the
same per-repo test command as the commit-test-gate (`scripts/test-cmd`), falling back to the
project's standard/documented test command when `scripts/test-cmd` is absent — never an improvised
command. After emitting a blocker the executor SHALL end the run and SHALL NOT start any remaining task.

#### Scenario: Stalled failure (rule a)
- **WHEN** the same test fails with the same normalized error signature after 2 consecutive fix attempts
- **THEN** the executor stops editing and emits a structured blocker

#### Scenario: Repeated touch (rule b)
- **WHEN** the executor is about to edit a file it has already edited twice for the same failure
- **THEN** the executor stops editing and emits a structured blocker

#### Scenario: Knowledge or artifact gap (rule c)
- **WHEN** a fix would require information/decisions absent from the artifacts, editing the frozen proposal/design, or contradicts `design.md`'s stated external-API behavior
- **THEN** the executor stops editing and emits a structured blocker

#### Scenario: Healthy iteration is not interrupted
- **WHEN** consecutive attempts produce *different* normalized error signatures (the failure is changing)
- **THEN** the executor keeps iterating and is NOT stopped
- **AND** it stays on the *same* failure (fix → re-run that failing test's module, not necessarily the whole suite), rather than advancing to another task

#### Scenario: Stopping ends the run
- **WHEN** the executor emits a `### NON-CONVERGENCE BLOCKER` for a task
- **THEN** it ends the run immediately and does NOT begin any remaining task

### Requirement: Non-convergence detection is deterministic, not in-context judgment
The rule (a) and (b) checks SHALL be computed by a helper script that normalizes the error signature
and maintains durable per-change state, so detection does not depend on the executor model's
in-context tracking. The executor SHALL pass the helper the raw test output and, when about to edit
a file, the `--editing <file>` input (load-bearing for rule (b)'s file-touch tracking). If the
helper cannot run or returns no parseable verdict, the executor SHALL treat that as a rule (c) gap
and stop.

#### Scenario: Cosmetic-only differences count as no progress
- **WHEN** two test outputs differ only in line numbers, paths, timestamps, or hex addresses
- **THEN** the normalizer yields the same signature (no progress), so rule (a) can trip

#### Scenario: Genuinely different failures stay distinct
- **WHEN** two attempts fail with substantively different errors
- **THEN** the normalizer yields different signatures and rule (a) does NOT trip

#### Scenario: Helper failure is fail-safe
- **WHEN** the convergence helper exits non-zero or emits no parseable verdict
- **THEN** the executor stops and emits a structured blocker with trigger `c` naming the helper failure

### Requirement: A declared blocker is machine-discriminable from an opaque give-up
On stopping, the executor SHALL emit a `### NON-CONVERGENCE BLOCKER` block carrying these distinct
fields: `trigger`, `task`, `test`, `signature`, `attempts`, `files`, `missing` (the blocking
info/decision/contradiction), and `suspected_cause` (a one-line diagnostic) — `missing` and
`suspected_cause` are separate fields, not merged. The primary SHALL distinguish a *declared* blocker
from an *opaque* give-up by detecting that exact heading in the completion report.

#### Scenario: Declared blocker present
- **WHEN** the completion report contains a `### NON-CONVERGENCE BLOCKER` block
- **THEN** the primary treats it as declared non-convergence and routes it to orchestrator triage

#### Scenario: Opaque give-up (Claude path)
- **WHEN** a non-crash failure occurs with no `### NON-CONVERGENCE BLOCKER` block on the Claude path
- **THEN** the primary treats it as an opaque give-up and falls back to the Sonnet subagent

#### Scenario: Opaque give-up (OpenCode path)
- **WHEN** a non-crash failure occurs with no `### NON-CONVERGENCE BLOCKER` block on the OpenCode path
- **THEN** the primary dispatches a fresh `@apply-executor` or escalates to the user (not Sonnet)

### Requirement: Recovery from a declared blocker is the orchestrator's decision
On a declared non-convergence blocker the primary SHALL choose recovery by triage rather than
reflexively escalating to Sonnet, on BOTH delegation paths. Triage options SHALL include: tighten
the brief / re-slice and dispatch a fresh executor (brief/plan gap); escalate to the user
(artifact/decision gap); or spawn a Sonnet subagent (model-capability gap).

#### Scenario: Claude delegation path
- **WHEN** the Claude-Code primary receives a declared blocker
- **THEN** it selects a triage branch (fresh executor / escalate / Sonnet) instead of auto-Sonnet

#### Scenario: OpenCode delegation path
- **WHEN** the OpenCode primary receives a declared blocker
- **THEN** it reports the blocker with the triage options to the user rather than silently waiting
