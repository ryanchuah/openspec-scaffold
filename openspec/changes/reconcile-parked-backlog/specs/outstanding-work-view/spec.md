## MODIFIED Requirements

### Requirement: plans-live-vs-archived-convention

The gather SHALL enumerate live plans **recursively** — every `plans/**/*.md` file, at any nesting depth
— while `plans/archive/**` SHALL denote shipped/closed plans and SHALL be excluded from the gather's live
list. A plan file nested under any subdirectory of `plans/` other than `archive/` SHALL be treated as
live and listed the same as a top-level `plans/*.md` file.

#### Scenario: archived plans excluded, live plans listed
- **WHEN** the repo has both `plans/foo.md` and `plans/archive/bar.md`
- **THEN** the snapshot SHALL list `plans/foo.md` as live and SHALL NOT list `plans/archive/bar.md`

#### Scenario: nested live plan is listed
- **WHEN** the repo has `plans/sub/item.md` (a plan nested inside a non-`archive` subdirectory)
- **THEN** the snapshot SHALL list `plans/sub/item.md` as live

#### Scenario: nested archived plans remain excluded
- **WHEN** the repo has `plans/archive/sub/old.md` (a plan nested inside `plans/archive/`)
- **THEN** the snapshot SHALL NOT list it, regardless of nesting depth under `plans/archive/`
