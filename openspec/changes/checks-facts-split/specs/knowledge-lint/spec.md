## MODIFIED Requirements

### Requirement: retired-path-tokens-extensible-per-repo

The config file name changes from `audit.toml` to `checks.toml`.

#### Scenario: defaults-used-when-no-config
- **WHEN** no `checks.toml` (or no `[knowledge_lint]` table) is present in the repo
- **THEN** the linter SHALL apply only its built-in default retired-path token set

#### Scenario: per-repo-tokens-extend-defaults
- **WHEN** `checks.toml` declares additional retired-path tokens under `[knowledge_lint]` via the `retired_paths` array key
- **THEN** the linter SHALL flag those tokens in addition to the built-in defaults (the `retired_paths` values are merged with, not replacing, the defaults)

### Requirement: knowledge-lint-tooling-is-scaffold-managed

The per-repo config file name changes from `audit.toml` to `checks.toml`.

#### Scenario: per-repo-config-not-scaffold-managed
- **WHEN** the manifest is checked for `checks.toml`
- **THEN** `checks.toml` SHALL NOT be a manifest entry (per-repo config stays per-repo)
