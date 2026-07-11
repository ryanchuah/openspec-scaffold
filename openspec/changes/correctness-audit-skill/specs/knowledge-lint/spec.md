# knowledge-lint — delta spec

## ADDED Requirements

### Requirement: linter-validates-audit-dossier-format
The deterministic linter SHALL validate correctness-audit dossiers, gated by an
explicit format marker: it scans `knowledge/research/correctness-audit-*/` directories
and SHALL check only those whose `CHARTER.md` contains the literal line
`format: correctness-audit/v1`. For marked dossiers it SHALL flag: (a) a finding ID
appearing more than once across the dossier's `FINDINGS*.md` files, (b) a census
disposition value outside the fixed set (`AUDITED-clean` / `AUDITED-finding` /
`LEAD-deferred` / `N/A-<reason>`), and (c) a graduated finding (any evidence label
other than `LEAD`) missing its `Prior:` or `Class:` field. A directory with no
`CHARTER.md`, or a `CHARTER.md` without the marker, SHALL be skipped entirely (legacy
hand-rolled dossiers pre-date the format and must not fail downstream gates); no
dossier directory at all SHALL lint clean. The check is detect-only.

#### Scenario: conforming dossier
- **WHEN** a marked dossier's FINDINGS files have unique IDs, valid census
  dispositions, and `Prior:`/`Class:` on every graduated finding
- **THEN** the check reports no findings

#### Scenario: duplicate finding ID across waves
- **WHEN** the same finding ID appears in two FINDINGS files of a marked dossier
- **THEN** the check flags the duplicate with both locations

#### Scenario: invalid census disposition
- **WHEN** a census row in a marked dossier carries a disposition outside the fixed set
- **THEN** the check flags the row

#### Scenario: graduated finding missing contract fields
- **WHEN** a finding in a marked dossier carries a non-`LEAD` evidence label but no
  `Prior:` or no `Class:` field
- **THEN** the check flags the finding; findings still labeled `LEAD` are not flagged
  for missing these fields

#### Scenario: legacy dossier without marker
- **WHEN** a `knowledge/research/correctness-audit-*/` directory exists whose
  `CHARTER.md` lacks the marker line, or which has no `CHARTER.md`
- **THEN** the check skips it entirely and reports no findings for it

#### Scenario: no dossier present
- **WHEN** the repo has no `knowledge/research/correctness-audit-*/` directory
- **THEN** the check reports no findings
