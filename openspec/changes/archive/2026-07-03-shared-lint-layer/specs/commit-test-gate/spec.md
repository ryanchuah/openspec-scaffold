## MODIFIED Requirements

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

## ADDED Requirements

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
