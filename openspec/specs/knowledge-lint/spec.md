## Purpose

Define the contract for detecting per-repo knowledge drift — prose and structure in tracked project
knowledge (`knowledge/`) that has fallen out of sync with reality. Two layers cover this: a
deterministic, stdlib-only linter (`scripts/knowledge_lint.py`) that catches structural/mechanical
drift, and an operator-invoked LLM judgment skill (`lint-knowledge`) that catches the semantic drift a
deterministic check cannot see. Both are detect-only — neither ever rewrites tracked prose — and both
are scaffold-managed, propagating byte-identical to every downstream repo via `sync_scaffold.py`.

## Requirements

### Requirement: deterministic-knowledge-linter-detects-drift

`scripts/knowledge_lint.py` SHALL be a stdlib-only linter that scans project knowledge and reports
per-repo knowledge drift **without modifying any file**. It SHALL scan the markdown files under
`knowledge/` for content checks, plus perform a repo-scoped check for orphaned canonical filenames. It
SHALL exit `0` when it finds no drift and exit `1` when it finds drift, printing one report line
per finding (path, and line number where the check is line-anchored). The checks are: orphan/duplicate
canonical files; retired-path tokens; broken prose path citations; dangling archive pointers; and a
guarded `knowledge/audit-log.md` registry-line format check.

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
repo-root `audit.toml` (via `tomllib`) when that file exists; when it is absent the built-in defaults
alone SHALL apply.

#### Scenario: defaults-used-when-no-config
- **WHEN** no `audit.toml` (or no `[knowledge_lint]` table) is present in the repo
- **THEN** the linter SHALL apply only its built-in default retired-path token set

#### Scenario: per-repo-tokens-extend-defaults
- **WHEN** `audit.toml` declares additional retired-path tokens under `[knowledge_lint]` via the `retired_paths` array key
- **THEN** the linter SHALL flag those tokens in addition to the built-in defaults (the `retired_paths` values are merged with, not replacing, the defaults)

### Requirement: judgment-layer-skill-detects-semantic-drift

A `lint-knowledge` skill SHALL exist at `.claude/skills/lint-knowledge/SKILL.md` (one path, discovered
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
- **WHEN** the `lint-knowledge` skill is invoked
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
- **THEN** it SHALL exist only at `.claude/skills/lint-knowledge/SKILL.md` (no `.opencode/` copy), and running it SHALL produce findings only, modifying no tracked file

### Requirement: knowledge-lint-tooling-is-scaffold-managed

The knowledge-lint tooling SHALL be scaffold-managed: `scripts/knowledge_lint.py`, its test file
`scripts/test_knowledge_lint.py`, and `.claude/skills/lint-knowledge/SKILL.md` SHALL be listed in
`scripts/scaffold_manifest.txt` so `scripts/sync_scaffold.py` propagates them byte-identical to every
downstream repo. The per-repo `audit.toml` SHALL NOT be added to the manifest (it is per-repo config,
not scaffold-managed).

#### Scenario: manifest-lists-linter-tooling
- **WHEN** `scripts/scaffold_manifest.txt` is read
- **THEN** it SHALL contain entries for `scripts/knowledge_lint.py`, `scripts/test_knowledge_lint.py`, and `.claude/skills/lint-knowledge/SKILL.md`

#### Scenario: per-repo-config-not-scaffold-managed
- **WHEN** the manifest is checked for `audit.toml`
- **THEN** `audit.toml` SHALL NOT be a manifest entry (per-repo config stays per-repo)
