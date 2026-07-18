# commit-test-gate — delta

## ADDED Requirements

### Requirement: A git-native pre-commit hook enforces the gate for every command spelling and every harness
The system SHALL enforce the single definition of green on every `git commit` via a git-native
`pre-commit` hook, independent of command spelling and independent of the agent harness. A tracked,
scaffold-managed `scripts/githooks/pre-commit` (byte-identical across repos) SHALL exec
`scripts/check.sh` and propagate its exit code so git blocks the commit when `check.sh` is non-zero.
The hook SHALL be wired via `git config --local core.hooksPath scripts/githooks` (the clone-safe
mechanism, since raw `.git/hooks/` is neither tracked nor copied on clone), performed by a
scaffold-managed `scripts/setup-hooks.sh`. Because git runs `pre-commit` regardless of how the commit
command is spelled and regardless of which harness issued it, this layer closes both the
prefix-evasion gap (`cd … && git commit`, `git -C … commit`, `env … git commit`) and the
cross-agent gap (non-Claude harnesses that never ran the `PreToolUse` hook).

#### Scenario: Prefix-evading command spellings are gated
- **WHEN** a `git commit` is attempted with `core.hooksPath` wired and `check.sh` failing, spelled as
  `cd <repo> && git commit`, `git -C <repo> commit`, or `env FOO=bar git commit`
- **THEN** git runs `scripts/githooks/pre-commit`, `check.sh` fails, and the commit is blocked

#### Scenario: A non-Claude harness commit is gated
- **WHEN** an OpenCode/DeepSeek (or operator-terminal) `git commit` is attempted with `core.hooksPath`
  wired and `check.sh` failing
- **THEN** git runs the pre-commit hook and blocks the commit (no dependency on a Claude-only hook)

#### Scenario: setup-hooks.sh is conflict-safe
- **WHEN** `scripts/setup-hooks.sh` runs and `core.hooksPath` is unset or already `scripts/githooks`
- **THEN** it sets (or confirms) `core.hooksPath=scripts/githooks` at `--local` scope and exits 0
- **AND WHEN** `core.hooksPath` already points at a different path
- **THEN** it warns and exits WITHOUT overwriting the developer's existing value

#### Scenario: --no-verify is a visible opt-out
- **WHEN** a `git commit --no-verify` is attempted
- **THEN** git skips the git-native pre-commit hook (an explicit, visible opt-out — distinct from the
  prior silent prefix-evasion)

### Requirement: The PreToolUse test-gate defers to the git-native hook, fail-safe
The Claude `PreToolUse` `scripts/test-gate.sh` SHALL remain wired as a defense-in-depth fallback and
SHALL no-op (exit 0 without running `check.sh`) ONLY when it positively confirms the git-native hook
will run for this commit; on any uncertainty it SHALL run `check.sh`. It SHALL defer only when ALL
hold: (1) the command is classified as a genuine `git commit` (not the UNKNOWN fallback); (2) the
command carries no `--no-verify` / short-flag cluster containing `n`; (3) git resolves a work tree and
the hook path from `git rev-parse --git-path hooks/pre-commit` (resolved from the worktree top) exists
and is executable. Every git invocation in the defer branch SHALL be guarded so that a git failure
falls through to running `check.sh` rather than aborting the gate. Consequently a normally-wired clone
SHALL run `check.sh` at most once per commit, and a clone without the git-native hook wired SHALL
still run the Claude-only gate (no silent regression).

#### Scenario: Defer when git-native is active (no double-run)
- **WHEN** a genuine `git commit` (no `--no-verify`) is attempted and `scripts/githooks/pre-commit` is
  present and executable at the configured `core.hooksPath`
- **THEN** `test-gate.sh` prints a defer notice and exits 0 without running `check.sh` (git-native runs
  it), so `check.sh` runs at most once

#### Scenario: Fallback when git-native is not wired (no regression)
- **WHEN** a genuine `git commit` is attempted and no executable pre-commit hook is resolvable
- **THEN** `test-gate.sh` runs `check.sh` and blocks the commit on failure, exactly as before this change

#### Scenario: --no-verify commits stay gated for Claude
- **WHEN** a `git commit --no-verify` (or `-n`) is attempted through the Claude Bash tool
- **THEN** `test-gate.sh` does NOT defer (git would skip the hook) and runs `check.sh` itself

#### Scenario: Git failure falls through to the gate (fail-safe)
- **WHEN** the defer branch's git resolution fails (git absent, not a repo, bare)
- **THEN** `test-gate.sh` does NOT abort or exit non-blocking; it falls through to running `check.sh`

## MODIFIED Requirements

### Requirement: Commits are gated on the project's tests
The system SHALL block a `git commit` when the project's configured tests do not pass. Primary
enforcement SHALL be a git-native `pre-commit` hook (`scripts/githooks/pre-commit` via
`core.hooksPath`) that runs the shared gate script for every command spelling and every harness; a
Claude Code `PreToolUse` hook on the `Bash` tool, narrowed to `git commit` (pattern
`Bash(git commit*)`, which also catches `git commit -am`, `--amend`, and similar forms), SHALL remain
as a fail-safe fallback that runs the shared gate script and blocks the tool call (hook exit code 2) on
failure when the git-native hook is not active. Either layer blocking on a non-green gate satisfies
this requirement.

#### Scenario: Tests fail
- **WHEN** a `git commit` is attempted and the configured test command exits non-zero
- **THEN** the commit is blocked and the failure summary is surfaced to the agent

#### Scenario: Tests pass
- **WHEN** a `git commit` is attempted and the configured test command exits zero
- **THEN** the commit proceeds

#### Scenario: No test command configured
- **WHEN** a `git commit` is attempted in a repo that has no `scripts/test-cmd`
- **THEN** the gate is a no-op and the commit proceeds

#### Scenario: Test command interpreter cannot be resolved
- **WHEN** `scripts/test-cmd` is present but its executable does not resolve (e.g. a fresh clone with no virtualenv)
- **THEN** the gate treats this as a configuration error, emits a warning, and does NOT block the commit

### Requirement: The gate ships with a smoke fixture and a documented wiring-smoke procedure
The repository SHALL carry a commit-test-gate smoke fixture and procedure that (a) exercises the gate
script's five branches, (b) documents how to smoke the Claude `PreToolUse` hook wiring in a gated
session, and (c) provides a **deterministic automated test of the git-native layer**. The script-layer
branches are deterministically testable; the Claude hook wiring (that Claude Code fires the
`PreToolUse` hook on `git commit`, that exit code 2 blocks, and that `$CLAUDE_PROJECT_DIR` expands)
requires a gated session and SHALL be a documented, repeatable operator procedure rather than an
automated test. The git-native layer, by contrast, SHALL be covered by an automated test
(`scripts/test_githook_pre_commit.py`) that builds a throwaway git repo, wires `core.hooksPath`, and
asserts commits are blocked (`check.sh` red) or allowed (green) across the prefix-evading spellings —
no gated session required.

#### Scenario: Script-layer branches are covered
- **WHEN** the gate script runs across its five `scripts/test-cmd` states
- **THEN** the smoke fixture confirms: absent → exit 0; empty/whitespace-only → exit 0; unresolvable executable → exit 0 with a warning; failing command → exit 2 (commit blocked); passing command → exit 0

#### Scenario: Wiring smoke is a documented gated-session procedure
- **WHEN** an operator needs to confirm the Claude `PreToolUse` hook actually fires on a real `git commit`
- **THEN** a documented procedure exists describing the failing-test→commit-blocked check, the passing-test→commit-allowed check, and the `$CLAUDE_PROJECT_DIR` expansion check, to be run in a gated session

#### Scenario: The git-native layer is covered by an automated test
- **WHEN** `scripts/test_githook_pre_commit.py` runs
- **THEN** it builds a throwaway repo with `core.hooksPath` wired and asserts commits are blocked when `check.sh` is red and allowed when green, across the `git commit`, `cd && git commit`, `git -C … commit`, and `env … git commit` spellings, with `--no-verify` documented as the visible opt-out — all without a gated Claude session

### Requirement: Instruction docs acknowledge the shipped gate hook
The scaffold's cross-agent-compatibility guidance SHALL NOT describe `.claude/settings.json` as
"hook-free". It SHALL acknowledge the commit-test gate's enforcement layers: the git-native
`pre-commit` hook (tracked, agent-neutral, honored by every harness — the primary layer) wired via
`core.hooksPath`, and the Claude-only `PreToolUse` `scripts/test-gate.sh` hook that defers to it as a
fail-safe fallback (a sanctioned carve-out recorded in `knowledge/decisions/INDEX.md`). Both run
tracked, agent-neutral scripts — so that an agent reconciling the instructions to the filesystem does
not read the present, tracked hooks as an invariant violation.

#### Scenario: Cross-agent guidance describes settings.json
- **WHEN** the cross-agent-compatibility section describes `.claude/settings.json` and commit enforcement
- **THEN** it states the git-native pre-commit hook is the primary agent-neutral gate and the `PreToolUse` test-gate hook is a sanctioned Claude-only fallback, and does NOT claim `.claude/settings.json` is "hook-free"

#### Scenario: Guidance omits settings.json entirely
- **WHEN** the cross-agent-compatibility guidance does not describe `.claude/settings.json` at all
- **THEN** no instruction text claims the file is "hook-free" (the requirement is satisfied by absence)
