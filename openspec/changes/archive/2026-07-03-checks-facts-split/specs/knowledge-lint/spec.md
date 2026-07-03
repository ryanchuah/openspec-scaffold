## MODIFIED Requirements

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
