## MODIFIED Requirements

### Requirement: linter-detects-closed-but-unpruned-entries

`scripts/knowledge_lint.py` SHALL flag a `knowledge/roadmap.md` `## ` entry or a `plans/**/*.md` file
(gathered recursively, at any nesting depth, excluding `plans/archive/**`) whose heading or
`**Priority:**`/`**Status:**` line carries a closed-token (`CLOSED`, `DONE`, `COMPLETE`, `✅`, or a
`~~…~~` struck-through heading), signalling it should graduate to the archive / `plans/archive/`. The
recursive gather and the `plans/archive/` exclusion SHALL agree with the `outstanding` fact's gather
(`scripts/outstanding.py`). Regardless of nesting depth, `plans/README.md` SHALL continue to be skipped
(it documents the taxonomy, not a plan). The finding SHALL be detect-only and flag-only, with a
`<!-- lint:keep -->` marker opting out a deliberately-retained closed note. It SHALL be wired into
`collect_findings()`.

#### Scenario: closed roadmap entry left in place is flagged
- **WHEN** a `knowledge/roadmap.md` `## ` entry's heading or priority/status line contains a closed-token and lacks a `<!-- lint:keep -->` marker
- **THEN** the linter SHALL flag it and exit `1`

#### Scenario: closed top-level plan file is flagged
- **WHEN** a top-level `plans/*.md` file carries a closed-token marker and is not under `plans/archive/`
- **THEN** the linter SHALL flag it

#### Scenario: closed nested plan file is flagged
- **WHEN** a plan file nested inside a non-`archive` subdirectory of `plans/` (e.g. `plans/sub/item.md`)
  carries a closed-token marker
- **THEN** the linter SHALL flag it the same as a top-level closed plan file

#### Scenario: lint:keep opts out
- **WHEN** the same closed entry carries a `<!-- lint:keep -->` marker
- **THEN** the linter SHALL NOT flag it
