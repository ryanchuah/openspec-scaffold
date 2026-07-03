## MODIFIED Requirements

### Requirement: each-knowledge-type-has-one-home

The project SHALL define a taxonomy of knowledge types, each with exactly one home, and the taxonomy (the types, the classification rule, and the home per type) SHALL be documented in a location reachable from the boot map (`AGENTS.md`). The homes SHALL be: state → `knowledge/STATUS.md` and `knowledge/questions/INDEX.md` (Active); mid-session handoff (an ephemeral, pre-archive session-continuation note) → `knowledge/HANDOFF.md`; decisions → `knowledge/decisions/INDEX.md`; questions → `knowledge/questions/`; lessons → `knowledge/lessons.md`; reference (durable facts not in code) → `knowledge/reference/`; research (synthesized investigation) → a dedicated indexed research home under `knowledge/`; roadmap → `knowledge/roadmap.md`; history → `openspec/changes/archive/`; contracts → `openspec/specs/`; rules → `.claude/skills/`, `openspec/config.yaml`, and `AGENTS.md` standing rules.

The mid-session handoff is distinct from state: `knowledge/STATUS.md` is reconciled once at archive by the archive-executor and is deliberately NOT written mid-change, so it cannot carry an in-flight, pre-archive handoff. `knowledge/HANDOFF.md` fills exactly that gap — a single blessed file a session writes when it must hand off mid-change (e.g. context exhausted before archive). It is ephemeral: the next session absorbs it and deletes it, so its normal state is absent. There SHALL be exactly one such file (superseding the ad-hoc practice of multiple root-level HANDOFF/HANDOVER files).

#### Scenario: taxonomy-documented-and-discoverable
- **WHEN** an agent needs to know where a kind of knowledge belongs
- **THEN** the taxonomy SHALL be documented and reachable via a pointer in `AGENTS.md`, without the agent having to infer it from existing file placement

#### Scenario: knowledge-filed-by-type
- **WHEN** a new decision is recorded
- **THEN** it SHALL be filed in `knowledge/decisions/INDEX.md`, and other knowledge types SHALL likewise be filed in the single home defined for their type

#### Scenario: reference-holds-not-in-code-facts
- **WHEN** content is durable but not recoverable from the source code — an operational runbook fact, an external-API or integration semantic, an empirical domain finding, or a specification for unbuilt work
- **THEN** it SHALL be filed under `knowledge/reference/`, distinct from `knowledge/research/` (which holds synthesized investigation) and `knowledge/lessons.md` (which holds process lessons)

#### Scenario: mid-session-handoff-has-single-home
- **WHEN** a session must hand off in-flight work before the change is archived (e.g. it runs out of context mid-change)
- **THEN** it SHALL write that handoff to the single file `knowledge/HANDOFF.md` — not to `knowledge/STATUS.md` (which is reconciled only at archive) and not to ad-hoc root-level HANDOFF/HANDOVER files
- **AND** the next session SHALL absorb the handoff and delete the file, so `knowledge/HANDOFF.md` is absent in the steady state

### Requirement: boot-files-each-answer-one-question

Each boot-read file SHALL answer exactly one question, and procedural rules that apply only within a phase SHALL NOT be boot reads. `AGENTS.md` answers "what is this project and where does everything live"; `knowledge/STATUS.md` answers "where are we right now"; `knowledge/questions/INDEX.md` (Active section) answers "what is blocking us". Additionally, when — and only when — `knowledge/HANDOFF.md` exists, it is a boot read answering "what mid-flight work must I resume", read immediately after `knowledge/STATUS.md`; because it is ephemeral (deleted on absorption) it adds nothing to the steady-state boot load. All knowledge types not designated as boot reads SHALL be loaded on demand — with history search-only and rules loaded on phase entry — never at boot.

#### Scenario: boot-set-is-minimal
- **WHEN** an agent boots into a repo
- **THEN** the mandatory boot reads SHALL be limited to `AGENTS.md`, `knowledge/STATUS.md`, and the Active section of `knowledge/questions/INDEX.md` — plus `knowledge/HANDOFF.md` if and only if that file exists

#### Scenario: mid-session-handoff-boot-read-when-present
- **WHEN** an agent boots into a repo where `knowledge/HANDOFF.md` is present
- **THEN** it SHALL read the handoff (immediately after `knowledge/STATUS.md`), absorb and continue the work it describes, and delete the file once absorbed
- **AND** when `knowledge/HANDOFF.md` is absent, the boot set SHALL be exactly the three mandatory files

#### Scenario: procedural-rules-not-at-boot
- **WHEN** a procedural rule applies only to a specific workflow phase
- **THEN** it SHALL live in that phase's skill (loaded on phase entry), not in a boot-read file

#### Scenario: non-boot-types-load-on-demand
- **WHEN** an agent needs decisions, lessons, reference, research, roadmap, or contracts
- **THEN** these SHALL be loaded on demand (not at boot), and history SHALL be reached by search rather than loaded
