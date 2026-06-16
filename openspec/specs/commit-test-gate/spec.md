## Purpose

Deterministically prevent commits when the project's tests are not green, via a Claude Code harness hook that runs a shared gate script — closing the gap where a delegated executor could claim tests pass without the orchestrator re-running them.

## Requirements

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

### Requirement: The orchestrator's verify re-run uses the single per-repo test command
The orchestrator's own full-suite re-run during verify SHALL source its command from the same per-repo
`scripts/test-cmd` as the commit-test-gate, falling back to the project's standard/documented test
command when `scripts/test-cmd` is absent — never a hard-coded or improvised command. The verify
instruction surfaces (the verify skill and `openspec/config.yaml`) SHALL cite `scripts/test-cmd` as
the source and present any concrete command (e.g. `pytest`) only as an illustrative example.

#### Scenario: Verify sources the command from test-cmd
- **WHEN** the orchestrator re-runs the full suite during verify
- **THEN** it runs the repo's `scripts/test-cmd` (or the documented fallback when absent), not a hard-coded command

#### Scenario: Instruction docs do not hard-code the verify command
- **WHEN** the verify skill or `openspec/config.yaml` describes the verify re-run
- **THEN** they reference `scripts/test-cmd` as the source and present any specific command only as an example

### Requirement: Instruction docs acknowledge the shipped gate hook
The scaffold's cross-agent-compatibility guidance SHALL NOT describe `.claude/settings.json` as
"hook-free". It SHALL acknowledge the shipped commit-test-gate `PreToolUse` hook as a sanctioned,
Claude-only carve-out (recorded in `ai-docs/decisions.md`) that runs a tracked, agent-neutral script —
so that an agent reconciling the instructions to the filesystem does not read the present, tracked
hook as an invariant violation.

#### Scenario: Cross-agent guidance describes settings.json
- **WHEN** the cross-agent-compatibility section describes `.claude/settings.json`
- **THEN** it states the commit-test-gate hook is present and sanctioned, and does NOT claim the file is "hook-free"

#### Scenario: Guidance omits settings.json entirely
- **WHEN** the cross-agent-compatibility guidance does not describe `.claude/settings.json` at all
- **THEN** no instruction text claims the file is "hook-free" (the requirement is satisfied by absence)
