## ADDED Requirements

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
