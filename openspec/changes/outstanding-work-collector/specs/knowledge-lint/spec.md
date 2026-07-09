## ADDED Requirements

### Requirement: linter-detects-duplicate-content-blocks

`scripts/knowledge_lint.py` SHALL flag a run of **≥ 8 consecutive non-trivial lines** that appear
identical (whitespace-normalized) in **two or more** files within a narrow compared set — markdown
under `knowledge/`, top-level `*.md`, and a per-repo-configurable `duplicate_scan_dirs` (read from the
`[knowledge_lint]` config table). It SHALL exclude `knowledge/research/` (period-correct history) and
`openspec/specs/` (legitimately shares scaffold spans). A `<!-- lint:dup-ok -->` marker whose line
falls inside a detected duplicate window SHALL suppress that finding. The check SHALL be detect-only
(never rewrites) and SHALL be wired into `collect_findings()`.

#### Scenario: verbatim block across two files is flagged
- **WHEN** the same ≥ 8-line non-trivial block appears in two in-scope files
- **THEN** the linter SHALL flag it (path + line of each occurrence) and exit `1`

#### Scenario: short, research-dir, or spec-dir repeats are not flagged
- **WHEN** the identical run is fewer than 8 lines, OR it appears inside `knowledge/research/`, OR it appears inside `openspec/specs/`
- **THEN** the linter SHALL NOT flag it

#### Scenario: dup-ok marker inside the window suppresses
- **WHEN** a `<!-- lint:dup-ok -->` marker line falls within a detected duplicate window
- **THEN** the linter SHALL NOT flag that block

### Requirement: linter-detects-closed-but-unpruned-entries

`scripts/knowledge_lint.py` SHALL flag a `knowledge/roadmap.md` `## ` entry or a top-level
`plans/*.md` file whose heading or `**Priority:**`/`**Status:**` line carries a closed-token
(`CLOSED`, `DONE`, `COMPLETE`, `✅`, or a `~~…~~` struck-through heading), signalling it should
graduate to the archive / `plans/archive/`. The finding SHALL be detect-only and flag-only, with a
`<!-- lint:keep -->` marker opting out a deliberately-retained closed note. It SHALL be wired into
`collect_findings()`.

#### Scenario: closed roadmap entry left in place is flagged
- **WHEN** a `knowledge/roadmap.md` `## ` entry's heading or priority/status line contains a closed-token and lacks a `<!-- lint:keep -->` marker
- **THEN** the linter SHALL flag it and exit `1`

#### Scenario: closed top-level plan file is flagged
- **WHEN** a top-level `plans/*.md` file carries a closed-token marker and is not under `plans/archive/`
- **THEN** the linter SHALL flag it

#### Scenario: lint:keep opts out
- **WHEN** the same closed entry carries a `<!-- lint:keep -->` marker
- **THEN** the linter SHALL NOT flag it

### Requirement: linter-detects-untriaged-finding-accumulation

`scripts/knowledge_lint.py` SHALL flag an untriaged finding (a finding ID present in a configured
`FINDINGS*` source but absent from `knowledge/questions/`) whose age exceeds `untriaged_max_age_days`
(from `[knowledge_lint]`, default 14). Age SHALL be derived from the containing `FINDINGS*` file's git
last-commit date, degrading to filesystem `mtime` when git is unavailable. The finding-extraction and
untriaged cross-reference SHALL be imported from the single shared implementation in
`scripts/outstanding.py` (API `extract_untriaged(root, config) -> list[dict]`) so the fact and the
linter never diverge. It SHALL be detect-only and wired into `collect_findings()`.

#### Scenario: stale untriaged finding is flagged
- **WHEN** an untriaged finding's containing file is older than `untriaged_max_age_days`
- **THEN** the linter SHALL flag it and exit `1`

#### Scenario: recent untriaged finding is not flagged
- **WHEN** the untriaged finding's containing file is within `untriaged_max_age_days`
- **THEN** the linter SHALL NOT flag it

#### Scenario: age falls back to mtime without git
- **WHEN** git is unavailable (e.g. a fixture tree with no `.git`)
- **THEN** the check SHALL derive the finding's age from the file's filesystem `mtime` rather than erroring

#### Scenario: shared extraction with the gather
- **WHEN** both the `outstanding` fact and this check evaluate the same repo
- **THEN** they SHALL agree on the untriaged set (identical extraction via `scripts/outstanding.py`)
