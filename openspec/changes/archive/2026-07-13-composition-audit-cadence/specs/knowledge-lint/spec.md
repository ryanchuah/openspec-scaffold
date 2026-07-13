# knowledge-lint — delta

## ADDED Requirements

### Requirement: audit-log-registry-line-accepts-composition-anchor-variant

The guarded `knowledge/audit-log.md` registry-line check SHALL accept exactly two line
formats:

- plain: `- **YYYY-MM-DD** · audit/YYYY-MM-DD · <short-sha> · <essence>`
- composition: `- **YYYY-MM-DD** · audit/YYYY-MM-DD-composition · <short-sha> · <essence>`

(the anchor pattern becomes `audit/<date>` optionally suffixed by `-composition`; the
short-sha remains 7–40 hex chars and the essence remains required non-empty). All other
lines SHALL continue to be flagged as malformed. This requirement pins the accepted
formats so the collision surface with other pending `knowledge-lint` deltas is visible
at archive time.

#### Scenario: composition-line-accepted
- **WHEN** `knowledge/audit-log.md` contains
  `- **2026-07-11** · audit/2026-07-11-composition · abc1234 · first composition pass`
- **THEN** the linter SHALL NOT flag the line

#### Scenario: plain-line-still-accepted
- **WHEN** the file contains a well-formed plain `audit/<date>` registry line
- **THEN** the linter SHALL NOT flag the line

#### Scenario: malformed-suffix-rejected
- **WHEN** a line carries any suffix other than `-composition` after the anchor date
  (e.g. `audit/2026-07-11-security`)
- **THEN** the linter SHALL flag the line as malformed
