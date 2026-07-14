## ADDED Requirements

### Requirement: Deterministic promotion of ADDED, REMOVED, and RENAMED operations
The archive-mechanization promoter SHALL apply ADDED, REMOVED, and RENAMED requirement-block operations from a change's delta specs into the canonical main specs deterministically, without invoking an LLM.

#### Scenario: ADDED requirement is appended
- **WHEN** a delta's `## ADDED Requirements` section names a requirement absent from the main spec
- **THEN** the promoter appends the requirement block under the main spec's `## Requirements` and records it as applied

#### Scenario: REMOVED requirement is deleted
- **WHEN** a delta's `## REMOVED Requirements` section names a requirement present in the main spec
- **THEN** the promoter deletes that requirement block from the main spec and records it as applied

#### Scenario: RENAMED requirement header is rewritten
- **WHEN** a delta's `## RENAMED Requirements` section supplies list items `- FROM: \`### Requirement: <old>\`` and `- TO: \`### Requirement: <new>\`` where the old header is present in the main spec and the new header is absent
- **THEN** the promoter rewrites only the requirement header line from the old name to the new name, leaving the body unchanged, and records it as applied

### Requirement: MODIFIED operations are deferred, never applied deterministically
The promoter SHALL NOT apply MODIFIED requirement operations, and it MUST emit each MODIFIED requirement in its report as deferred for LLM merge.

#### Scenario: a MODIFIED requirement is reported as deferred
- **WHEN** a delta contains a `## MODIFIED Requirements` section
- **THEN** the promoter leaves the corresponding main-spec requirement unchanged and lists that requirement name under `deferred_modified` in its report

#### Scenario: RENAMED and MODIFIED on the same requirement in one delta
- **WHEN** a single delta both RENAMEs a requirement from `X` to `Y` and MODIFIEs `Y`
- **THEN** the promoter applies the rename first (so the main spec now holds `Y`) and reports `Y` under `deferred_modified` without attempting the merge, guaranteeing the deterministic rename precedes the LLM merge

### Requirement: Anomalous operations halt promotion and leave specs unwritten
When any operation across the change's delta specs is anomalous, the promoter MUST write no changes to any main spec and MUST exit with code 2, reporting every anomaly.

#### Scenario: ADDED name collides with a different existing body
- **WHEN** a delta ADDs a requirement whose name already exists in the main spec with a materially different body
- **THEN** the promoter reports an anomaly, writes nothing to any main spec, and exits with code 2

#### Scenario: two ADDED blocks for the same name within one delta differ
- **WHEN** a single delta's `## ADDED Requirements` section contains two `### Requirement:` blocks with the same name but different bodies
- **THEN** the promoter reports an anomaly, writes nothing to any main spec, and exits with code 2 (the same rule as a main-spec collision applies within one delta; two identical such blocks would instead be a skip)

#### Scenario: RENAMED target is ambiguous
- **WHEN** a RENAMED operation's `FROM` and `TO` requirements are both present, or both absent, in the main spec
- **THEN** the promoter reports an anomaly, writes nothing to any main spec, and exits with code 2

#### Scenario: REMOVED or RENAMED targets a capability with no main spec file
- **WHEN** a REMOVED or RENAMED operation targets a capability whose `openspec/specs/<capability>/spec.md` does not exist
- **THEN** the promoter reports an anomaly (there is nothing to modify), writes nothing, and exits with code 2

#### Scenario: one anomaly blocks an otherwise-clean delta set
- **WHEN** a change's delta specs contain one applicable operation and one anomalous operation
- **THEN** the promoter writes no changes to any main spec and exits with code 2

### Requirement: Already-satisfied operations are reported as skips, not anomalies
An operation whose intended end-state already holds in the main spec SHALL be reported as a skip and MUST NOT be treated as an anomaly.

#### Scenario: REMOVED target is already absent
- **WHEN** a REMOVED operation names a requirement that is not present in the main spec
- **THEN** the promoter records a skip with reason target-absent and does not treat it as an anomaly

#### Scenario: ADDED requirement already present with an equivalent body
- **WHEN** an ADDED requirement's name already exists in the main spec with an equivalent body — comparing the two blocks with per-line trailing whitespace stripped and leading and trailing blank lines trimmed
- **THEN** the promoter records a skip and makes no change

#### Scenario: RENAMED is already applied
- **WHEN** a RENAMED operation's `FROM` requirement is absent and its `TO` requirement is present
- **THEN** the promoter records a skip and makes no change

### Requirement: New main specs are created for ADDED requirements on unknown capabilities
When an ADDED requirement targets a capability that has no main spec, the promoter SHALL create the main spec with a Purpose and Requirements skeleton before appending the requirement.

#### Scenario: ADDED-only delta for a new capability
- **WHEN** a delta ADDs requirements for a capability with no existing `openspec/specs/<capability>/spec.md`
- **THEN** the promoter creates the main spec with a `## Purpose` and `## Requirements` skeleton, appends the ADDED requirements, and records the spec as created

### Requirement: Parsing tolerates skeleton main specs and degenerate deltas
The promoter SHALL parse a main spec that has a `## Purpose` but no `## Requirements` header as having zero requirements, and it MUST treat a delta section that contains no requirement blocks as a clean no-op rather than an error.

#### Scenario: main spec has a Purpose but no Requirements header
- **WHEN** the main spec exists with a `## Purpose` but no `## Requirements` header, and a delta ADDs a requirement to it
- **THEN** the promoter inserts a `## Requirements` header before appending the block, and does not crash; a REMOVED against that spec is a skip (target absent) and a RENAMED whose source is absent is an anomaly

#### Scenario: empty or header-only delta
- **WHEN** a delta contains a section header (e.g. `## ADDED Requirements`) with no requirement block beneath it, or contains no delta section headers at all
- **THEN** the promoter completes as a clean no-op, writing nothing and exiting zero

### Requirement: The promoter serves both callers and supports a no-write dry run
The promoter SHALL accept a change directory and a main-specs root as inputs so both the archive executor and the standalone sync-specs skill can invoke it, and it MUST support a dry-run mode that plans and reports without writing. The report distinguishes applied, skipped, deferred (MODIFIED), and anomalous operations; its JSON schema is documented in the promoter's `--help` output (the canonical machine contract for both callers).

#### Scenario: dry-run writes nothing
- **WHEN** the promoter is invoked in dry-run mode against a change with pending delta operations
- **THEN** it reports the full plan and exit code but makes no change to any main spec

#### Scenario: invocation works from an active or archived change directory
- **WHEN** the promoter is given the path to a change directory containing `specs/<capability>/spec.md`, whether that directory is the active change dir or the archived copy
- **THEN** it discovers and promotes the delta specs identically

### Requirement: Deterministic change-directory move with a conflict guard
The archive-mechanization mover SHALL move a change directory to its archive path only when the destination does not already exist, and it MUST exit non-zero without moving anything when the destination already exists.

#### Scenario: move succeeds when the destination is absent
- **WHEN** the mover is given an existing change directory and an archive path that does not yet exist
- **THEN** it creates the archive parent directory as needed, moves the change directory to the archive path, and exits zero

#### Scenario: destination already exists
- **WHEN** the mover is given an archive path that already exists
- **THEN** it exits non-zero and moves nothing, reporting the conflict
