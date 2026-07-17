## Purpose

Define the contract for a deterministic, complete, on-demand snapshot of all outstanding work across a project
repository. The `outstanding` fact (a `facts.py` regenerate-on-use snapshot, never-stale) mechanically
enumerates every configured source — `knowledge/questions/` (Active + Parked), non-archive `openspec/changes/*/tasks.md`
unchecked items, `plans/`, `knowledge/roadmap.md` non-closed entries, and audit `FINDINGS*` files — into a
single `output/facts/outstanding.{md,json}` snapshot with `source:line` provenance. An untriaged-findings bucket
surfaces Fable/similar findings the moment they are written, separate from triaged work. The companion
`outstanding-work-scan` skill (agent-neutral, pull-only, zero boot-context cost) runs the gather and drives
LLM judgment. The gather is scaffold-managed and propagates byte-identical to downstream repos via
`sync_scaffold.py`.

## Requirements
### Requirement: gather-produces-complete-never-failing-snapshot

The `outstanding` fact SHALL enumerate every configured outstanding-work source into a snapshot and
SHALL NEVER exit non-zero on account of source content. The fact is a `kind="delegate"`,
`family="fact"` entry (`facts.py --check outstanding`) whose logic lives in `scripts/outstanding.py`.
It SHALL write a human-readable `output/facts/outstanding.md` and a machine-readable
`output/facts/outstanding.json`, regenerating both on every run (undated, overwritten), and every
emitted item SHALL carry `source:line` provenance. The guarantee is completeness of the source set
within the fact family's graceful-degradation bounds — not item extraction from prose.

#### Scenario: clean run writes both artifacts
- **WHEN** `facts.py --check outstanding` runs against a repo with well-formed sources
- **THEN** it SHALL exit `0` and write both `output/facts/outstanding.md` and `output/facts/outstanding.json`
- **AND** each listed item SHALL record the source file and line it came from

#### Scenario: malformed source degrades, never crashes
- **WHEN** a scanned source cannot be parsed
- **THEN** the fact SHALL emit an explicit `UNPARSEABLE — read manually: <path> (<reason>)` entry and SHALL still exit `0`
- **AND** the malformed source SHALL NOT be silently dropped from the snapshot

#### Scenario: regenerate-on-use reflects current state
- **WHEN** an outstanding item is resolved at its source and the fact is re-run
- **THEN** the regenerated snapshot SHALL no longer list that item, with no manual edit to any snapshot file

### Requirement: structured-extraction-is-format-plural-with-point-only-fallback

The gather SHALL extract structured one-liners from `knowledge/questions/INDEX.md` in **both** list
form and table form, and SHALL fall back to point-only enumeration (file + first heading + git
metadata) for sources with no recognized structure, never fabricating items from prose.

#### Scenario: bullet-form Active items extracted
- **WHEN** `INDEX.md`'s Active section uses markdown list items (`- `/`* `/`1. `)
- **THEN** each item SHALL appear in the snapshot with its provenance

#### Scenario: table-form Active items extracted
- **WHEN** `INDEX.md`'s Active section uses a markdown table (rows that are not the header or the `---` separator)
- **THEN** each row SHALL be extracted as an item (the gather SHALL NOT require list form)

#### Scenario: prose-only source enumerated point-only
- **WHEN** a `knowledge/questions/<item>.md` per-item file or a `plans/` plan file has no structured item list
- **THEN** the gather SHALL enumerate the file (path + first heading + git tracked/mtime state) as a single "read this" entry and SHALL NOT invent line-items from its prose

### Requirement: findings-are-first-class-with-a-separate-untriaged-bucket

A finding SHALL be reported in a distinct **untriaged** bucket, separate from triaged open work, when
its ID matches the configured pattern in a configured `FINDINGS*` source but appears nowhere under
`knowledge/questions/`. The untriaged scan SHALL cover both `knowledge/questions/INDEX.md` and every
`knowledge/questions/*.md` per-item file.

#### Scenario: untriaged finding surfaces immediately
- **WHEN** a finding ID exists in a `FINDINGS*` file but is not referenced anywhere under `knowledge/questions/`
- **THEN** it SHALL appear in the snapshot's untriaged bucket, not the triaged open-work list

#### Scenario: triaging moves a finding out of the untriaged bucket
- **WHEN** that finding ID is subsequently referenced in any `knowledge/questions/` file and the fact is re-run
- **THEN** it SHALL NOT appear in the untriaged bucket

### Requirement: per-repo-configuration-with-graceful-defaults

The gather SHALL read fact-consumed settings from a `[facts.outstanding]` table (`findings_globs`,
`finding_id_pattern`) and SHALL run with documented defaults when the table or `checks.toml` is
absent. An unconfigured or non-matching findings scheme SHALL yield an empty untriaged bucket, never
an error, and the snapshot SHALL surface the active config plus a findings-files-scanned vs. IDs-
matched count so a zero-match against non-empty files is visible.

#### Scenario: absent config runs on defaults
- **WHEN** the repo has no `checks.toml`
- **THEN** `facts.py --check outstanding` SHALL run cleanly on defaults and exit `0`

#### Scenario: per-repo finding scheme honored and visible
- **WHEN** a repo sets `finding_id_pattern` to its own scheme
- **THEN** the gather SHALL match findings by that pattern
- **AND** SHALL report the count of findings-files scanned and IDs matched (so a non-empty file with zero matches is detectable)

### Requirement: plans-live-vs-archived-convention

The gather SHALL enumerate live plans **recursively** — every `plans/**/*.md` file, at any nesting
depth — while `plans/archive/**` SHALL denote shipped/closed plans and SHALL be excluded from the
gather's live list. A plan file nested under any subdirectory of `plans/` other than `archive/`
SHALL be treated as live and listed the same as a top-level `plans/*.md` file.

#### Scenario: archived plans excluded, live plans listed
- **WHEN** the repo has both `plans/foo.md` and `plans/archive/bar.md`
- **THEN** the snapshot SHALL list `plans/foo.md` as live and SHALL NOT list `plans/archive/bar.md`

#### Scenario: nested live plan is listed
- **WHEN** the repo has `plans/sub/item.md` (a plan nested inside a non-`archive` subdirectory)
- **THEN** the snapshot SHALL list `plans/sub/item.md` as live

#### Scenario: nested archived plans remain excluded
- **WHEN** the repo has `plans/archive/sub/old.md` (a plan nested inside `plans/archive/`)
- **THEN** the snapshot SHALL NOT list it, regardless of nesting depth under `plans/archive/`

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

### Requirement: composition-audit-due-signal-block

The `outstanding` fact SHALL expose a standalone top-level `composition_audit` block —
not a virtual source in the enumeration — carrying the composition-audit due-signal:
`anchor_tag`, `archived_changes_since`, `commits_since`, `thresholds`, `due`, `reason`,
`status`, and `computed_from: "git"` (explicit provenance, since the block is computed
from git state rather than enumerated from a configured source). The rendered markdown
SHALL include a `## Composition audit` section, placed directly under the header when
`due` and at the bottom otherwise. Signal semantics (anchor discovery, counting rules,
thresholds and their defaults, degradation) are normative in the `composition-audit`
capability spec — this block SHALL conform to them and SHALL NOT restate them. The
block SHALL be advisory only and SHALL never affect the fact's exit behavior
(fact-family entries never fail).

#### Scenario: due-signal-present-and-typed
- **WHEN** the `outstanding` fact regenerates in a git repo
- **THEN** the JSON payload SHALL contain the `composition_audit` block with all named
  fields and the markdown SHALL contain the `## Composition audit` section

#### Scenario: due-state-is-prominent
- **WHEN** the signal computes `due: true`
- **THEN** the `## Composition audit` section SHALL appear directly under the
  snapshot header with the reason line

#### Scenario: not-due-renders-at-bottom
- **WHEN** the signal computes `due: false`
- **THEN** the `## Composition audit` section SHALL appear at the bottom of the
  rendered markdown, after the enumerated sections

#### Scenario: degraded-signal-never-fails-the-fact
- **WHEN** git is unavailable or the anchor is unreachable
- **THEN** the fact SHALL still regenerate cleanly, with the block carrying the
  degraded `status`/`reason` per the composition-audit spec
