<!-- This delta augments the `commit-test-gate` capability defined in openspec/specs/commit-test-gate/spec.md. -->

## ADDED Requirements

### Requirement: The gate ships with a smoke fixture and a documented wiring-smoke procedure
The repository SHALL carry a commit-test-gate smoke fixture and procedure that (a) exercises the gate script's five branches and (b) documents how to smoke the hook wiring in a gated Claude session. The script-layer branches are deterministically testable; the hook wiring (that Claude Code fires the `PreToolUse` hook on `git commit`, that exit code 2 blocks, and that `$CLAUDE_PROJECT_DIR` expands) requires a gated session and SHALL be a documented, repeatable operator procedure rather than an automated test.

#### Scenario: Script-layer branches are covered
- **WHEN** the gate script runs across its five `scripts/test-cmd` states
- **THEN** the smoke fixture confirms: absent → exit 0; empty/whitespace-only → exit 0; unresolvable executable → exit 0 with a warning; failing command → exit 2 (commit blocked); passing command → exit 0

#### Scenario: Wiring smoke is a documented gated-session procedure
- **WHEN** an operator needs to confirm the hook actually fires on a real `git commit`
- **THEN** a documented procedure exists describing the failing-test→commit-blocked check, the passing-test→commit-allowed check, and the `$CLAUDE_PROJECT_DIR` expansion check, to be run in a gated session
