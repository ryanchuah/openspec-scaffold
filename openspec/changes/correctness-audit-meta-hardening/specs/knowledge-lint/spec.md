## ADDED Requirements

### Requirement: linter-detects-audit-liveness-drift
`scripts/knowledge_lint.py` SHALL flag, as a drift finding, a marked correctness-audit dossier that is still in-progress but is not referenced by any Active item in `knowledge/questions/INDEX.md`. It SHALL scan `knowledge/research/correctness-audit-*/` directories and consider only those whose `CHARTER.md` contains the literal marker line `format: correctness-audit/v1`; among those, a dossier is in-progress when its `CHARTER.md` does not contain a `status: closed` line. For an in-progress dossier, the check SHALL confirm the dossier directory name appears in the Active section of `knowledge/questions/INDEX.md` (the region from the `## Active` heading to the next `## ` heading); if it does not, the check SHALL flag the dossier. A directory with no `CHARTER.md`, a `CHARTER.md` without the format marker, or a `CHARTER.md` marked `status: closed` SHALL be skipped; no dossier directory at all SHALL lint clean. The check is detect-only and SHALL be wired into `collect_findings()`.

#### Scenario: in-progress dossier missing its Active item is flagged
- **WHEN** a marked dossier's `CHARTER.md` lacks a `status: closed` line and the dossier directory name does not appear in the `## Active` section of `knowledge/questions/INDEX.md`
- **THEN** the linter SHALL flag the dossier as liveness drift and exit `1`

#### Scenario: in-progress dossier with an Active item is clean
- **WHEN** the in-progress dossier's directory name appears in the Active section of `knowledge/questions/INDEX.md`
- **THEN** the linter SHALL NOT flag it

#### Scenario: closed dossier needs no Active item
- **WHEN** a marked dossier's `CHARTER.md` contains a `status: closed` line
- **THEN** the check skips it and SHALL NOT require an Active questions item

#### Scenario: unmarked or absent dossier lints clean
- **WHEN** a `correctness-audit-*` directory lacks the format marker, or no such directory exists
- **THEN** the check reports no findings

### Requirement: linter-validates-post-close-audit-ledger
`scripts/knowledge_lint.py` SHALL validate a post-close audit ledger's line format when one is present in a marked dossier, gated on presence so un-adopted repos lint clean. It SHALL scan marked `knowledge/research/correctness-audit-*/` dossiers (those whose `CHARTER.md` carries `format: correctness-audit/v1`) for a `POST-CLOSE-LEDGER.md` file; when that file is absent the check SHALL report nothing. When the file is present, each ledger entry line — every line that is not blank, not a markdown heading, not a table-separator row, and not an HTML comment — SHALL, after stripping a single optional leading and trailing `|`, split on `|` into at least five cells each non-empty after trimming, corresponding to `commit | subsystem | wave-owner | spec? | review-tier`; a line that does not SHALL be flagged with its line number. The check SHALL accept both the bare form (`a | b | c | d | e`) and the pipe-delimited table form (`| a | b | c | d | e |`). The check is detect-only and SHALL be wired into `collect_findings()`.

#### Scenario: well-formed ledger line is clean
- **WHEN** a `POST-CLOSE-LEDGER.md` in a marked dossier contains an entry line with all five non-empty pipe-separated fields
- **THEN** the linter SHALL NOT flag it

#### Scenario: malformed ledger line is flagged
- **WHEN** a ledger entry line is missing one or more of the five fields (fewer than five pipe-separated cells, or an empty cell)
- **THEN** the linter SHALL flag the line with its line number and exit `1`

#### Scenario: header and separator rows are not entries
- **WHEN** a `POST-CLOSE-LEDGER.md` line is a markdown heading, a table-separator row, an HTML comment, or blank
- **THEN** the check SHALL NOT treat it as an entry line and SHALL NOT flag it

#### Scenario: absent ledger lints clean
- **WHEN** a marked dossier has no `POST-CLOSE-LEDGER.md`, or no `correctness-audit-*` dossier directory exists at all
- **THEN** the check reports no findings
