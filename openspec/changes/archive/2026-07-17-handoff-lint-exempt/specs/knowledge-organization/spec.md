## MODIFIED Requirements

### Requirement: each-knowledge-type-has-one-home

The project SHALL define a taxonomy of knowledge types, each with exactly one home, and the taxonomy (the types, the classification rule, and the home per type) SHALL be documented in a location reachable from the boot map (`AGENTS.md`). The homes SHALL be: state → `knowledge/STATUS.md` and `knowledge/questions/INDEX.md` (Active); mid-session handoff (an ephemeral, pre-archive session-continuation note) → `knowledge/HANDOFF.md`; decisions → `knowledge/decisions/INDEX.md`; questions → `knowledge/questions/`; lessons → `knowledge/lessons.md`; reference (durable facts not in code) → `knowledge/reference/`; research (synthesized investigation) → a dedicated indexed research home under `knowledge/`; roadmap → `knowledge/roadmap.md`; history → `openspec/changes/archive/`; contracts → `openspec/specs/`; rules → `.claude/skills/`, `openspec/config.yaml`, and `AGENTS.md` standing rules.

The mid-session handoff is distinct from state: `knowledge/STATUS.md` is reconciled once at archive by the archive-executor and is deliberately NOT written mid-change, so it cannot carry an in-flight, pre-archive handoff. `knowledge/HANDOFF.md` fills exactly that gap — a single blessed file a session writes when it must hand off mid-change (e.g. context exhausted before archive). It is ephemeral: the next session absorbs it and deletes it, so its normal state is absent. There SHALL be exactly one such file (superseding the ad-hoc practice of multiple root-level HANDOFF/HANDOVER files).

The handoff is a forward-looking work order, not steady-state knowledge. Because it exists to tell the next session what to build, its prose necessarily resolves against a future tree rather than the current one — it forward-references not-yet-created files, names the archive dir its in-flight change will land in, and carries quoted context forward so the next session need not re-read the source. Deterministic knowledge-hygiene tooling SHALL therefore treat `knowledge/HANDOFF.md` as out of scope when scanning it as a **source**, in both directions of the existing ephemeral carve-out: a citation *to* the handoff is not broken merely because the file is absent, and prose *within* the handoff is not drift merely because it names paths that do not exist yet. Absent this, the tooling that gates commits would make the mandated handoff un-committable, and the only route to a green tree would be to delete it.

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

#### Scenario: ephemeral-handoff-citation-exempt-from-citation-integrity-tooling
- **WHEN** deterministic citation-integrity tooling that resolves knowledge path citations against disk — specifically `scripts/knowledge_lint.py` (its broken-prose-path-citation check) and `scripts/sync_scaffold.py --check-refs` (its dangling-reference check) — scans a file that cites `knowledge/HANDOFF.md` (e.g. `knowledge/README.md` and `AGENTS.md` name it in the taxonomy and boot instruction)
- **THEN** that tooling SHALL treat `knowledge/HANDOFF.md` as a known-ephemeral path and SHALL NOT report the citation as broken/dangling merely because the file is absent, since absence is its designed steady state
- **AND** citations to other non-existent knowledge paths SHALL still be flagged (the exemption is scoped to the known-ephemeral handoff path, not a blanket suppression)

#### Scenario: handoff-prose-exempt-when-scanned-as-a-source
- **WHEN** the same deterministic tooling — `scripts/knowledge_lint.py` and `scripts/sync_scaffold.py --check-refs` — scans `knowledge/HANDOFF.md` itself as a source file, and its prose forward-references not-yet-created paths, names a not-yet-created archive dir, carries a retired-path token, or quotes a block from another knowledge file
- **THEN** that tooling SHALL NOT report those as findings, since a handoff's prose resolves against the future tree it describes rather than the current one
- **AND** the live-tree gate SHALL stay green with the handoff present, so a session that writes a handoff can commit it
- **AND** the identical prose in any other knowledge file SHALL still be flagged (the exemption is scoped to the sanctioned handoff path, not a blanket suppression)
