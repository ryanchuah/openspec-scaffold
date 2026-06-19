## MODIFIED Requirements

### Requirement: manifest-declares-shared-files

A file `scripts/scaffold_manifest.txt` in the scaffold repo SHALL be the authoritative list of all
scaffold-managed files. Each line is a repo-relative path; lines starting with `#` and blank lines are
comments. The manifest SHALL be itself scaffold-managed (listed in itself). It SHALL list only files that
exist in the scaffold repo. Adding a new scaffold-managed file SHALL require updating the manifest and
re-running `sync_scaffold.py` for each downstream repo.

#### Scenario: manifest-lists-itself
- **WHEN** `scripts/scaffold_manifest.txt` exists in the scaffold repo
- **THEN** `scripts/scaffold_manifest.txt` SHALL appear as an entry in that file

#### Scenario: manifest-excludes-volatile-state
- **WHEN** the manifest lists all scaffold-managed files
- **THEN** it SHALL NOT include any per-repo project knowledge under `knowledge/` — specifically
  `knowledge/STATUS.md`, the `knowledge/decisions/` tree, the `knowledge/questions/` tree, `knowledge/lessons.md`,
  `knowledge/roadmap.md`, the `knowledge/reference/` tree, and the `knowledge/research/` tree — nor
  `.claude/settings.json`, `scripts/test-cmd`, or `scripts/sync_scaffold.py` (the sync script lives in
  scaffold only)
- **AND** the sole exception under `knowledge/` is `knowledge/README.md` — the universal taxonomy map — which IS
  scaffold-managed (see `manifest-includes-taxonomy-map`)

#### Scenario: manifest-includes-taxonomy-map
- **WHEN** `scripts/scaffold_manifest.txt` lists scaffold-managed files
- **THEN** `knowledge/README.md` SHALL be an entry in the manifest and SHALL be synced byte-identical to
  downstream repos, so the knowledge taxonomy (types, classification rule, home table) stays consistent
  across all repos rather than drifting per-repo

#### Scenario: manifest-includes-scaffold-check
- **WHEN** `scripts/scaffold_manifest.txt` lists scaffold-managed files
- **THEN** `scripts/scaffold_check.py` SHALL be an entry in the manifest and SHALL be synced to downstream
  repos as a scaffold-managed file (the pre-commit hook in downstream repos depends on it)

#### Scenario: manifest-comment-lines-ignored
- **WHEN** `scripts/sync_scaffold.py` or `scripts/scaffold_check.py` processes the manifest
- **THEN** lines beginning with `#` and blank lines SHALL be skipped

#### Scenario: manifest-lists-only-existing-scaffold-files
- **WHEN** a path is listed in the manifest
- **THEN** that path SHALL exist in the scaffold repo
- **AND** a file that is scaffold-managed in principle but absent from scaffold SHALL NOT be listed until
  it exists in scaffold
