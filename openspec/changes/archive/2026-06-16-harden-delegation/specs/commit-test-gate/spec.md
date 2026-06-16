## ADDED Requirements

### Requirement: Commits are gated on the project's tests
The system SHALL block an orchestrator `git commit` when the project's configured tests do not pass.
Enforcement SHALL be a Claude Code `PreToolUse` hook on the `Bash` tool, narrowed to `git commit`
(pattern `Bash(git commit*)`, which also catches `git commit -am`, `--amend`, and similar forms),
that runs the shared gate script and blocks the tool call (hook exit code 2) on failure.

#### Scenario: Tests fail
- **WHEN** the orchestrator attempts a `git commit` and the configured test command exits non-zero
- **THEN** the commit is blocked and the failure summary is surfaced to the agent

#### Scenario: Tests pass
- **WHEN** the orchestrator attempts a `git commit` and the configured test command exits zero
- **THEN** the commit proceeds

#### Scenario: No test command configured
- **WHEN** a `git commit` is attempted in a repo that has no `scripts/test-cmd`
- **THEN** the gate is a no-op and the commit proceeds

#### Scenario: Test command interpreter cannot be resolved
- **WHEN** `scripts/test-cmd` is present but its executable does not resolve (e.g. a fresh clone with no virtualenv)
- **THEN** the gate treats this as a configuration error, emits a warning, and does NOT block the commit

### Requirement: The gate is shared logic with a single per-repo value
The gate script SHALL be byte-identical across repos. The only per-repo value SHALL be the test
command, supplied via a one-line `scripts/test-cmd` file that is NOT shared.

#### Scenario: Same script, per-repo command
- **WHEN** the gate runs in any repo
- **THEN** it executes the same shared `scripts/test-gate.sh`
- **AND** it reads the command to run from that repo's own `scripts/test-cmd`
