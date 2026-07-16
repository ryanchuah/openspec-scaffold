## MODIFIED Requirements

### Requirement: pull-only-agent-neutral-invocation

The capability SHALL be invoked on demand through the scaffold-managed `outstanding-work-scan`
skill under `.claude/skills/` (auto-discovered by both Claude and OpenCode), and SHALL NOT be wired
into any boot-loaded file (no session-start hook, no procedure embedded in `AGENTS.md`), so it
carries zero boot-context cost.

#### Scenario: skill is the invocation surface
- **WHEN** the operator wants the outstanding-work view
- **THEN** the `outstanding-work-scan` skill SHALL exist under `.claude/skills/`, run the gather, and consume `output/facts/outstanding.json`

#### Scenario: no boot-path wiring
- **WHEN** the scaffold's mandatory-read boot set is inspected (`AGENTS.md`, `knowledge/STATUS.md`, `knowledge/questions/INDEX.md` Active)
- **THEN** none SHALL embed the gather procedure as a standing instruction (at most a one-line pointer to the skill)
