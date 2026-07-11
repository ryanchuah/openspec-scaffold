# outstanding-work-view — delta

## ADDED Requirements

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
