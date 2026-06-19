## MODIFIED Requirements

### Requirement: each-knowledge-type-has-one-home

The project SHALL define a taxonomy of knowledge types, each with exactly one home, and the taxonomy (the types, the classification rule, and the home per type) SHALL be documented in a location reachable from the boot map (`AGENTS.md`). The homes SHALL be: state → `knowledge/STATUS.md` and `knowledge/questions/INDEX.md` (Active); decisions → `knowledge/decisions/INDEX.md`; questions → `knowledge/questions/`; lessons → `knowledge/lessons.md`; reference (durable facts not in code) → `knowledge/reference/`; research (synthesized investigation) → a dedicated indexed research home under `knowledge/`; roadmap → `knowledge/roadmap.md`; history → `openspec/changes/archive/`; contracts → `openspec/specs/`; rules → `.claude/skills/`, `openspec/config.yaml`, and `AGENTS.md` standing rules.

#### Scenario: taxonomy-documented-and-discoverable
- **WHEN** an agent needs to know where a kind of knowledge belongs
- **THEN** the taxonomy SHALL be documented and reachable via a pointer in `AGENTS.md`, without the agent having to infer it from existing file placement

#### Scenario: knowledge-filed-by-type
- **WHEN** a new decision is recorded
- **THEN** it SHALL be filed in `knowledge/decisions/INDEX.md`, and other knowledge types SHALL likewise be filed in the single home defined for their type

#### Scenario: reference-holds-not-in-code-facts
- **WHEN** content is durable but not recoverable from the source code — an operational runbook fact, an external-API or integration semantic, an empirical domain finding, or a specification for unbuilt work
- **THEN** it SHALL be filed under `knowledge/reference/`, distinct from `knowledge/research/` (which holds synthesized investigation) and `knowledge/lessons.md` (which holds process lessons)

### Requirement: boot-files-each-answer-one-question

Each boot-read file SHALL answer exactly one question, and procedural rules that apply only within a phase SHALL NOT be boot reads. `AGENTS.md` answers "what is this project and where does everything live"; `knowledge/STATUS.md` answers "where are we right now"; `knowledge/questions/INDEX.md` (Active section) answers "what is blocking us". All knowledge types not designated as boot reads SHALL be loaded on demand — with history search-only and rules loaded on phase entry — never at boot.

#### Scenario: boot-set-is-minimal
- **WHEN** an agent boots into a repo
- **THEN** the mandatory boot reads SHALL be limited to `AGENTS.md`, `knowledge/STATUS.md`, and the Active section of `knowledge/questions/INDEX.md`

#### Scenario: procedural-rules-not-at-boot
- **WHEN** a procedural rule applies only to a specific workflow phase
- **THEN** it SHALL live in that phase's skill (loaded on phase entry), not in a boot-read file

#### Scenario: non-boot-types-load-on-demand
- **WHEN** an agent needs decisions, lessons, reference, research, roadmap, or contracts
- **THEN** these SHALL be loaded on demand (not at boot), and history SHALL be reached by search rather than loaded

### Requirement: migration-preserves-not-in-code-knowledge

A restructuring or cleanup SHALL NOT delete knowledge that cannot be recovered from the source code. Any such content inside a directory slated for removal SHALL be relocated to its taxonomy home before that directory is deleted.

#### Scenario: rescue-before-delete
- **WHEN** a directory slated for deletion (e.g. `docs/`) contains content that cannot be recovered from the source code
- **THEN** that content SHALL be moved to its taxonomy home (e.g. `knowledge/reference/`) before the directory is deleted

#### Scenario: code-derivable-directory-deletable
- **WHEN** every file in a directory slated for deletion is recoverable from the source code
- **THEN** the directory MAY be deleted without relocation

### Requirement: archive-step-reconciles-into-new-structure

The archive step SHALL reconcile current project state into the new structure — `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`, and `knowledge/questions/` — and SHALL NOT write to the legacy `STATUS.md` (root) or `ai-docs/` paths.

#### Scenario: archive-updates-memory-state
- **WHEN** a change is archived
- **THEN** the archive step SHALL update `knowledge/STATUS.md`, append the decision to `knowledge/decisions/INDEX.md`, and reconcile `knowledge/questions/` (Active/Parked)

#### Scenario: decisions-index-entry-points-to-archive
- **WHEN** a decision is appended to `knowledge/decisions/INDEX.md` during archiving
- **THEN** the entry SHALL be a one-line registry entry that points to the change archive holding the full rationale (or carries the rationale inline when no archive exists)

#### Scenario: questions-horizon-split-on-archive
- **WHEN** a change is archived and leaves follow-on items
- **THEN** blocking items SHALL remain in `knowledge/questions/INDEX.md` (Active) and non-blocking items SHALL be moved to Parked, so the boot-read Active section holds only current blockers
