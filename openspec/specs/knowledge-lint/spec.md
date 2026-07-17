## Purpose

Define the contract for detecting per-repo knowledge drift — prose and structure in tracked project
knowledge (`knowledge/`) that has fallen out of sync with reality. Two layers cover this: a
deterministic, stdlib-only linter (`scripts/knowledge_lint.py`) that catches structural/mechanical
drift, and an operator-invoked LLM judgment skill (`knowledge-drift-review`) that catches the
semantic drift a deterministic check cannot see. Both are detect-only — neither ever rewrites
tracked prose — and both are scaffold-managed, propagating byte-identical to every downstream repo
via `sync_scaffold.py`. The deterministic linter's citation matcher is hardened against
false-positives on legitimate notation, a `<!-- lint:planned -->` marker suppresses forward-reference
citations, a repo-wide handoff-file check mechanizes the handoff-file convention, and the linter is gated
on the live repository tree via pytest.

## Requirements

### Requirement: deterministic-knowledge-linter-detects-drift

`scripts/knowledge_lint.py` SHALL be a stdlib-only linter that scans project knowledge and reports
per-repo knowledge drift **without modifying any file**. It SHALL scan the markdown files under
`knowledge/` for content checks, plus perform a repo-scoped check for orphaned canonical filenames. It
SHALL exit `0` when it finds no drift and exit `1` when it finds drift, printing one report line
per finding (path, and line number where the check is line-anchored). The checks are: orphan/duplicate
canonical files; retired-path tokens; broken prose path citations; dangling archive pointers; a
guarded `knowledge/audit-log.md` registry-line format check; and a handoff-file check.

#### Scenario: orphan-or-duplicate-canonical-file-flagged
- **WHEN** a canonical filename from the linter's fixed single-home canonical set (`STATUS.md → knowledge/STATUS.md`, `lessons.md → knowledge/lessons.md`, `roadmap.md → knowledge/roadmap.md`, `audit-log.md → knowledge/audit-log.md`) exists as a file **outside** its taxonomy home (e.g. a root `STATUS.md`), or a second copy of a canonical file exists
- **THEN** the linter SHALL flag it as an orphan/duplicate finding
- **AND** `INDEX.md` and `README.md` SHALL NOT be in the canonical set (they have multiple legitimate homes, so a basename match would false-positive)

#### Scenario: retired-path-token-flagged
- **WHEN** a tracked knowledge file contains a retired-path token from the active token set (built-in defaults include `ai-docs/`, `plans/open-issues.md`, `docs/reviews/`, `/home/me/`)
- **THEN** the linter SHALL flag the file and line of the occurrence

#### Scenario: broken-prose-path-citation-flagged
- **WHEN** a knowledge file contains a **backtick-wrapped, repo-relative** path-like token (contains a `/` or ends in `.md`; NOT a URL, NOT an absolute system path) **whose first path segment is an existing top-level directory under the root** (e.g. `` `plans/gone/` `` where `plans/` exists) — that does not resolve to an existing path on disk
- **THEN** the linter SHALL flag the unresolved citation
- **AND** a bare (non-backtick) mention, a URL, or an absolute system path SHALL NOT be treated as a citation (deliberately conservative window to bound false positives)

#### Scenario: citation-first-segment-must-be-real-top-level-dir
- **WHEN** a backtick-wrapped token's first path segment is NOT an existing top-level directory under the root — a bare filename (`` `tasks.md` ``), a cross-repo name (`` `extrends/AGENTS.md` ``), GitHub shorthand (`` `sst/opencode` ``), or a non-path slashy token (`` `WHEN/THEN/AND` ``)
- **THEN** the linter SHALL NOT flag it (this first-segment gate is the load-bearing control that keeps the check usable against real prose)

#### Scenario: git-ignored-paths-skipped
- **WHEN** the root is a git repository and a file (e.g. a vendored/ignored reference clone) is git-ignored
- **THEN** the linter SHALL NOT scan or flag it; when git is unavailable (e.g. a test fixture tree) nothing is skipped

#### Scenario: research-dir-excluded-from-content-checks
- **WHEN** a retired-path token or an unresolved backtick path citation appears inside `knowledge/research/` (period-correct historical analyses that legitimately cite pre-restructure paths)
- **THEN** the linter SHALL NOT flag it, while the same token or citation outside `knowledge/research/` SHALL be flagged (the retired-path and broken-citation content checks exclude `knowledge/research/`, mirroring `sync_scaffold.py`'s reference-scan exclusion)

#### Scenario: dangling-archive-pointer-flagged
- **WHEN** a tracked knowledge file references an `openspec/changes/archive/<dir>/` path that does not exist
- **THEN** the linter SHALL flag the dangling pointer

#### Scenario: audit-log-registry-check-is-guarded
- **WHEN** `knowledge/audit-log.md` exists and one of its entry lines does not match the registry-line format
- **THEN** the linter SHALL flag that line
- **AND WHEN** `knowledge/audit-log.md` does not exist, the linter SHALL skip this check and SHALL NOT error

#### Scenario: clean-exit-zero
- **WHEN** the linter finds no drift across all checks
- **THEN** it SHALL exit `0`

#### Scenario: drift-exit-nonzero
- **WHEN** the linter finds one or more drift findings
- **THEN** it SHALL exit `1` and report every finding

### Requirement: knowledge-linter-is-detect-only

`scripts/knowledge_lint.py` SHALL NOT write to, create, edit, or delete any file under any flag or
input. Its only effects SHALL be its printed report and its process exit code. This preserves the
detect-only posture: the linter surfaces drift for a human/agent to fix, and never rewrites prose.

#### Scenario: working-tree-unchanged-after-run
- **WHEN** `knowledge_lint.py` runs, whether it finds drift or not
- **THEN** the scanned file tree SHALL be byte-identical before and after the run (no file created, modified, or deleted)

### Requirement: retired-path-tokens-extensible-per-repo

The linter SHALL ship a built-in default retired-path token set and SHALL additionally honor a
per-repo extension so a downstream repo can register its own retired paths **without editing the
scaffold-managed script**. The extension SHALL be read from an optional `[knowledge_lint]` table in a
repo-root `checks.toml` (via `tomllib`) when that file exists; when it is absent the built-in defaults
alone SHALL apply.

#### Scenario: defaults-used-when-no-config
- **WHEN** no `checks.toml` (or no `[knowledge_lint]` table) is present in the repo
- **THEN** the linter SHALL apply only its built-in default retired-path token set

#### Scenario: per-repo-tokens-extend-defaults
- **WHEN** `checks.toml` declares additional retired-path tokens under `[knowledge_lint]` via the `retired_paths` array key
- **THEN** the linter SHALL flag those tokens in addition to the built-in defaults (the `retired_paths` values are merged with, not replacing, the defaults)

### Requirement: judgment-layer-skill-detects-semantic-drift

A `knowledge-drift-review` skill SHALL exist at `.claude/skills/knowledge-drift-review/SKILL.md` (one path, discovered
by both the Claude and OpenCode harnesses; no `.opencode/` copy) defining an operator-invoked LLM
judgment pass that detects the drift a deterministic linter cannot see. It SHALL FIRST run
`scripts/knowledge_lint.py` to clear the cheap deterministic findings, and only THEN perform the LLM
judgment sweeps (so the expensive pass is not spent on drift the linter already catches). It SHALL be
**detect-only** (it produces findings and SHALL NOT rewrite prose) and SHALL be a periodic/on-demand
pass — NOT run on every archive. Its judgment sweeps SHALL cover: (a) stale "not yet built / planned /
designed-not-built" claims that contradict a shipped `openspec/changes/archive/` entry or
`knowledge/STATUS.md`; (b) intra-doc contradictions; (c) buried operator/pre-prod items present in a
README/runbook but absent from `knowledge/questions/INDEX.md` Active.

#### Scenario: deterministic-pass-runs-first
- **WHEN** the `knowledge-drift-review` skill is invoked
- **THEN** it SHALL run `scripts/knowledge_lint.py` before beginning its LLM judgment sweeps

#### Scenario: stale-not-built-claim-flagged
- **WHEN** a tracked doc describes a feature as "not yet built"/"planned" that a shipped archive entry or `knowledge/STATUS.md` records as shipped
- **THEN** the skill SHALL flag the contradiction

#### Scenario: intra-doc-contradiction-flagged
- **WHEN** two passages within one tracked doc assert contradictory facts (e.g. two lists of different length for the same set)
- **THEN** the skill SHALL flag the intra-doc contradiction

#### Scenario: buried-gate-item-flagged
- **WHEN** a README/runbook names a real operator or pre-production gate that is absent from `knowledge/questions/INDEX.md` Active
- **THEN** the skill SHALL flag the buried item

#### Scenario: skill-ships-single-path-detect-only
- **WHEN** the skill is added to the scaffold
- **THEN** it SHALL exist only at `.claude/skills/knowledge-drift-review/SKILL.md` (no `.opencode/` copy), and running it SHALL produce findings only, modifying no tracked file

### Requirement: knowledge-lint-tooling-is-scaffold-managed

The knowledge-lint tooling SHALL be scaffold-managed: `scripts/knowledge_lint.py`, its test file
`scripts/test_knowledge_lint.py`, and `.claude/skills/knowledge-drift-review/SKILL.md` SHALL be listed in
`scripts/scaffold_manifest.txt` so `scripts/sync_scaffold.py` propagates them byte-identical to every
downstream repo. The per-repo `checks.toml` SHALL NOT be added to the manifest (it is per-repo config,
not scaffold-managed).

#### Scenario: manifest-lists-linter-tooling
- **WHEN** `scripts/scaffold_manifest.txt` is read
- **THEN** it SHALL contain entries for `scripts/knowledge_lint.py`, `scripts/test_knowledge_lint.py`, and `.claude/skills/knowledge-drift-review/SKILL.md`

#### Scenario: per-repo-config-not-scaffold-managed
- **WHEN** the manifest is checked for `checks.toml`
- **THEN** `checks.toml` SHALL NOT be a manifest entry (per-repo config stays per-repo)

### Requirement: The broken-citation check skips legitimate citation notation
The broken-prose-path-citation check SHALL NOT false-positive on legitimate citation notation (this
becomes load-bearing because the live-tree gate promotes `knowledge_lint.py` to a commit gate).
Extending the existing skip-ladder (which
already skips URLs, absolute paths, globs, `{…}` placeholders, non-path tokens, first-segment-not-a-
real-dir, and `EPHEMERAL_PATHS`), the check SHALL additionally treat the following as non-findings:
(a) brace-expansion patterns `{a,b}` and `{a..b}`; (b) literal date/period placeholders such as
`YYYY-Www`; (c) a trailing `::symbol` node-id (pytest/symbol reference) — resolved by stripping the
`::` suffix and existence-checking the file; (d) a trailing `:N-M` line range — resolved by stripping
the range and existence-checking the file; and (e) any citation rooted under the `output/` ephemeral
prefix. Each skip SHALL remain narrow enough that a genuinely-missing file still flags.

#### Scenario: brace-expansion patterns are not flagged
- **WHEN** a knowledge doc cites `` `eval/labels/2026-W2{3,4,5}.yaml` `` or `` `output/notability-eval.{md,json}` ``
- **THEN** the linter SHALL NOT flag it (a brace pattern is a deliberate notation, not a broken path)

#### Scenario: period placeholders are not flagged
- **WHEN** a doc cites `` `eval/labels/YYYY-Www.yaml` `` or `` `output/digest-{label}.md` ``
- **THEN** the linter SHALL NOT flag it

#### Scenario: symbol node-ids resolve against the file
- **WHEN** a doc cites `` `src/trendscope/extract.py::_normalize_tokens` `` and `src/trendscope/extract.py` exists
- **THEN** the linter SHALL NOT flag it (the `::symbol` suffix is stripped before the existence check)
- **AND WHEN** the underlying file does not exist, it SHALL still flag as genuine drift

#### Scenario: line ranges resolve against the file
- **WHEN** a doc cites `` `src/trendscope/scoring.py:490-524` `` and `src/trendscope/scoring.py` exists
- **THEN** the linter SHALL NOT flag it (the `:N-M` range is stripped before the existence check)

#### Scenario: single-line number resolves like a range
- **WHEN** a doc cites `` `src/trendscope/utils.py:42` `` (a single line number, not a range) and `src/trendscope/utils.py` exists
- **THEN** the linter SHALL NOT flag it (the `:N` suffix is stripped before the existence check, same as `:N-M`)
- **AND WHEN** the underlying file does not exist (e.g. `` `src/trendscope/gone.py:42` ``), it SHALL still flag as genuine drift

#### Scenario: output artifacts are ephemeral
- **WHEN** a doc cites a concrete path under `output/` (e.g. `` `output/digest-2026-W25.md` ``)
- **THEN** the linter SHALL NOT flag it (`output/` is treated as an ephemeral prefix)

#### Scenario: genuinely missing files still flag
- **WHEN** a doc cites `` `src/trendscope/gone.py` `` under a real top-level dir and the file does not exist and matches none of the skip forms
- **THEN** the linter SHALL still flag the unresolved citation (hardening does not blind the check to real drift)

### Requirement: An inline lint:planned marker suppresses forward-reference citations
`knowledge_lint.py` SHALL skip broken-prose-path-citation findings on any line containing the literal
`<!-- lint:planned -->` marker, so a doc can deliberately forward-reference a not-yet-created file
without tripping the commit gate. The suppression SHALL be line-scoped: a marker on one line does not
affect other lines.

#### Scenario: marked line is not flagged
- **WHEN** a knowledge doc line cites `` `src/pending.py` `` (which does not exist) and the same line also contains `<!-- lint:planned -->`
- **THEN** the linter SHALL NOT flag that line (the marker suppresses the finding)

#### Scenario: unmarked line is still flagged
- **WHEN** the same broken citation `` `src/pending.py` `` appears on a line that does NOT contain the marker
- **THEN** the linter SHALL still flag the unresolved citation

#### Scenario: suppression does not leak to other lines
- **WHEN** line 1 cites `` `src/gone.py` `` without the marker and line 3 cites `` `src/other.py` `` with the marker
- **THEN** line 1's broken citation SHALL still be flagged despite the marker on line 3

### Requirement: Handoff-named files are flagged
`knowledge_lint.py` SHALL flag any non-gitignored file anywhere in the repository whose name
contains `handoff` or `handover` (case-insensitive substring match), mechanizing the
knowledge-handoff-file decision that exactly one sanctioned handoff file may exist. The
sanctioned ephemeral `knowledge/HANDOFF.md` SHALL be the sole exemption; every other
handoff-named file — at any depth, tracked or merely present in the working tree — SHALL be
flagged. Gitignored paths SHALL NOT be scanned (consistent with the other repo-wide checks), so
transient handoff-named files under ignored directories are out of scope for this check. This
check rides the same live-tree gate as the other doc-lints.

#### Scenario: a nested handoff-named file is flagged
- **WHEN** a file whose name contains `handoff` (any case) exists at any path outside
  `knowledge/HANDOFF.md` and is not gitignored — e.g. `plans/session-handoff.md`
- **THEN** the linter SHALL flag it as a finding

#### Scenario: a handover-named file is matched case-insensitively
- **WHEN** a non-gitignored file named e.g. `docs/HANDOVER.md` or `tmp/session-Handover.md` exists
- **THEN** the linter SHALL flag it as a finding

#### Scenario: the sanctioned in-tree handoff is exempt
- **WHEN** `knowledge/HANDOFF.md` exists (the sanctioned mid-session handoff location)
- **THEN** the linter SHALL NOT flag it

#### Scenario: gitignored handoff files are not scanned
- **WHEN** a handoff-named file exists under a gitignored path — e.g. `output/x-handoff.md`
- **THEN** the linter SHALL NOT flag it

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

### Requirement: linter-detects-claims-ledger-staleness
The deterministic knowledge linter (`scripts/knowledge_lint.py`) SHALL detect staleness of a `product-audit/v1`-marked claims ledger by comparing the recorded content hash of each covered promise-surface file against the file's current content. The detector SHALL glob `knowledge/reference/*.md` and, for each file containing the literal marker `format: product-audit/v1`, parse its `## Covered promise-surface files` manifest (entries of the form `- <path> — sha256:<64-hex>`); for each parseable entry it SHALL flag a finding when the covered file is missing, or when the file's current `sha256` (of its raw bytes) differs from the recorded hash. The detector SHALL be marker-gated so a repo with no `product-audit/v1` ledger produces zero findings, keeping this repo and un-adopted downstream repos lint-clean under the live-tree gate. A manifest line that does not parse to a path plus a 64-hex sha256 SHALL be silently skipped (the detector guards staleness, not manifest format), and a validly-marked ledger with no manifest section or an empty manifest SHALL produce zero findings. The detector SHALL check staleness of *listed* files only — manifest completeness (a promise-surface file present on disk but absent from the manifest) is a coverage concern outside its scope. Like every knowledge-lint detector, it is detect-only, never rewrites tracked content, and SHALL be wired into `collect_findings()`.

#### Scenario: covered file drifted since reconciliation
- **WHEN** a `product-audit/v1`-marked claims ledger lists a covered file whose current content sha256 differs from the recorded hash
- **THEN** the linter emits a `claims-ledger-staleness` finding naming the drifted file

#### Scenario: listed covered file is missing
- **WHEN** the manifest lists a covered file that no longer exists on disk
- **THEN** the linter emits a `claims-ledger-staleness` finding naming the missing file

#### Scenario: no marked ledger keeps the tree clean
- **WHEN** a repo has no file under `knowledge/reference/` carrying `format: product-audit/v1`
- **THEN** the detector emits zero findings

#### Scenario: malformed and vacuous manifests are tolerated
- **WHEN** a marked ledger has a manifest line that is not `- <path> — sha256:<64-hex>`, or has no manifest section, or an empty manifest section
- **THEN** the detector silently skips the unparseable line(s) and emits zero findings for a vacuous manifest

### Requirement: The sanctioned handoff is exempt from prose-hygiene checks as a scanned source
`knowledge_lint.py` SHALL exempt the file `knowledge/HANDOFF.md` from every prose-hygiene check that evaluates its content against the current state of the tree — specifically `retired-path-token`, `broken-prose-path-citation`, `dangling-archive-pointer`, and `duplicate-content-block`. The sanctioned mid-session handoff is a forward-looking work order, not steady-state knowledge: it exists to tell the next session what to build, so it necessarily forward-references not-yet-created files, names the archive dir its in-flight change will land in, and carries quoted context forward. This mirrors the existing `knowledge/research/` content-check exclusion, whose rationale is the mirror image (period-correct historical prose legitimately cites paths that no longer exist), extended to the two additional scan sets a handoff also trips. The exemption SHALL be keyed to the exact repo-relative path `knowledge/HANDOFF.md` — not a substring match, not any handoff-named file, and not a `knowledge/` prefix — so drift in every other knowledge doc still flags. Structural and named-file checks (orphan/duplicate-filename, audit-log, ratchet-log, ledger checks) SHALL be unaffected.

This exemption is load-bearing rather than cosmetic: the live-tree gate promotes `knowledge_lint.py` to a commit gate, so without it a session that writes a handoff cannot commit it, and the only route to a green tree is to delete the handoff — defeating the handoff mechanism the `knowledge-organization` spec mandates.

#### Scenario: a handoff's forward-referencing prose is not flagged
- **WHEN** `knowledge/HANDOFF.md` exists and cites a not-yet-created path (e.g. `` `.claude/skills/pending/SKILL.md` ``), contains a retired-path token (e.g. `ai-docs/`), names a not-yet-created archive dir (e.g. `openspec/changes/archive/2026-07-18-pending/`), and quotes a ≥8-line block from another knowledge file
- **THEN** the linter SHALL report zero findings for `knowledge/HANDOFF.md`

#### Scenario: the quoted file takes no collateral duplicate finding
- **WHEN** `knowledge/HANDOFF.md` carries forward a ≥8-line quoted block from another knowledge file (e.g. `knowledge/README.md`)
- **THEN** the linter SHALL NOT report a `duplicate-content-block` finding against that quoted file on account of the handoff, since the handoff is excluded from the compared set

#### Scenario: a handoff present on the live tree keeps the gate green
- **WHEN** a `knowledge/HANDOFF.md` of the shape above is present on the live tree
- **THEN** the live-tree lint gate SHALL pass, so the handoff is committable

#### Scenario: the identical drift in a non-handoff knowledge file still flags
- **WHEN** the same broken citation, retired-path token, planned archive pointer, or duplicated block appears in any knowledge file other than `knowledge/HANDOFF.md` (e.g. `knowledge/reference/notes.md`)
- **THEN** the linter SHALL still flag it (the exemption is scoped to the sanctioned handoff path, not a blanket suppression)

#### Scenario: a handoff-named file elsewhere is exempt from neither check family
- **WHEN** a handoff-named file exists under `knowledge/` at a path other than the sanctioned one (e.g. `knowledge/session-handoff.md`) and contains a broken citation
- **THEN** the linter SHALL flag it under the handoff-named-file check AND SHALL still flag its broken citation (the prose-hygiene exemption keys on the exact path `knowledge/HANDOFF.md`, so it does not extend to other handoff-named files)
- **AND** a handoff-named file outside `knowledge/` (e.g. `plans/session-handoff.md`) SHALL still be flagged by the handoff-named-file check, which walks the whole tree; its prose is not citation-checked there because `broken-prose-path-citation` scans only `knowledge/**/*.md` by design — a pre-existing scan-domain boundary unrelated to this exemption
