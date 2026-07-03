## Purpose

Deterministically prevent commits when the project's tests are not green, via a Claude Code harness hook that runs a shared gate script — closing the gap where a delegated executor could claim tests pass without the orchestrator re-running them. The gate now delegates to `scripts/check.sh` (the single shared definition of green — lint, format, and tests) and fires only on genuine `git commit` invocations, not arbitrary Bash carrying the substring.

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
The gate SHALL run the repo's single definition of green: the scaffold-managed
`scripts/test-gate.sh` (hook-invoked) SHALL delegate to the scaffold-managed `scripts/check.sh`,
which runs `ruff check` + `ruff format --check` + the repo's tests via `scripts/test-cmd`. Both
`test-gate.sh` and `check.sh` SHALL be byte-identical across repos; the only per-repo value SHALL
remain the test command in the one-line `scripts/test-cmd` file (NOT shared). Consequently a lint
violation or a format drift SHALL block a commit exactly as a failing test does.

#### Scenario: Same script, per-repo command
- **WHEN** the gate runs in any repo
- **THEN** it executes the same shared `scripts/test-gate.sh` → `scripts/check.sh`
- **AND** it reads the command for the test stage from that repo's own `scripts/test-cmd`

#### Scenario: Lint or format failure blocks the commit
- **WHEN** the orchestrator attempts a `git commit` and `ruff check` or `ruff format --check` fails (even with tests green)
- **THEN** the commit is blocked and the failing stage is surfaced to the agent

#### Scenario: Tests still gate through check.sh
- **WHEN** the orchestrator attempts a `git commit` and the repo's `scripts/test-cmd` exits non-zero
- **THEN** the commit is blocked (check.sh propagates the non-zero test result)

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
Claude-only carve-out (recorded in `knowledge/decisions/INDEX.md`) that runs a tracked, agent-neutral script —
so that an agent reconciling the instructions to the filesystem does not read the present, tracked
hook as an invariant violation.

#### Scenario: Cross-agent guidance describes settings.json
- **WHEN** the cross-agent-compatibility section describes `.claude/settings.json`
- **THEN** it states the commit-test-gate hook is present and sanctioned, and does NOT claim the file is "hook-free"

#### Scenario: Guidance omits settings.json entirely
- **WHEN** the cross-agent-compatibility guidance does not describe `.claude/settings.json` at all
- **THEN** no instruction text claims the file is "hook-free" (the requirement is satisfied by absence)

### Requirement: The gate ships with a smoke fixture and a documented wiring-smoke procedure
The repository SHALL carry a commit-test-gate smoke fixture and procedure that (a) exercises the gate script's five branches and (b) documents how to smoke the hook wiring in a gated Claude session. The script-layer branches are deterministically testable; the hook wiring (that Claude Code fires the `PreToolUse` hook on `git commit`, that exit code 2 blocks, and that `$CLAUDE_PROJECT_DIR` expands) requires a gated session and SHALL be a documented, repeatable operator procedure rather than an automated test.

#### Scenario: Script-layer branches are covered
- **WHEN** the gate script runs across its five `scripts/test-cmd` states
- **THEN** the smoke fixture confirms: absent → exit 0; empty/whitespace-only → exit 0; unresolvable executable → exit 0 with a warning; failing command → exit 2 (commit blocked); passing command → exit 0

#### Scenario: Wiring smoke is a documented gated-session procedure
- **WHEN** an operator needs to confirm the hook actually fires on a real `git commit`
- **THEN** a documented procedure exists describing the failing-test→commit-blocked check, the passing-test→commit-allowed check, and the `$CLAUDE_PROJECT_DIR` expansion check, to be run in a gated session

### Requirement: The commit gate fires only on a genuine git commit invocation
The `PreToolUse` matcher SHALL gate only an actual `git commit` command, NOT arbitrary Bash that
merely contains the substring `git commit` inside a redirection, an `echo`, a heredoc, or another
non-commit payload. This closes the parked misfire where complex non-commit orchestration commands
were intermittently blocked while a suite was red mid-change. The commit-test-gate smoke fixture
SHALL carry a must-not-gate regression probe reproducing that misfire.

#### Scenario: Complex non-commit Bash carrying the substring is not gated
- **WHEN** a non-commit Bash command runs that contains `git commit` only as a substring (e.g. a harmless payload with file redirections and an EXIT-sentinel echo)
- **THEN** the gate SHALL NOT fire and the command SHALL run ungated

#### Scenario: A genuine commit still gates
- **WHEN** an actual `git commit` (including `git commit -am`, `--amend`) is attempted with the suite red
- **THEN** the gate SHALL fire and block the commit

#### Scenario: The misfire is a smoke-fixture regression probe
- **WHEN** the commit-test-gate smoke fixture runs
- **THEN** it SHALL include the reproduction command as a must-not-gate probe, so a matcher regression is caught
