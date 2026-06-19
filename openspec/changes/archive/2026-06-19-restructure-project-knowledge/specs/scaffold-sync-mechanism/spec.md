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
- **THEN** it SHALL NOT include any per-repo project knowledge under `memory/` — specifically
  `memory/STATUS.md`, the `memory/decisions/` tree, the `memory/questions/` tree, `memory/lessons.md`,
  `memory/roadmap.md`, the `memory/reference/` tree, and the `memory/research/` tree — nor
  `.claude/settings.json`, `scripts/test-cmd`, or `scripts/sync_scaffold.py` (the sync script lives in
  scaffold only)
- **AND** the sole exception under `memory/` is `memory/README.md` — the universal taxonomy map — which IS
  scaffold-managed (see `manifest-includes-taxonomy-map`)

#### Scenario: manifest-includes-taxonomy-map
- **WHEN** `scripts/scaffold_manifest.txt` lists scaffold-managed files
- **THEN** `memory/README.md` SHALL be an entry in the manifest and SHALL be synced byte-identical to
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

### Requirement: sync-script-copies-files

`scripts/sync_scaffold.py <target-repo-path>` SHALL copy every manifest-listed file from the scaffold root
to the corresponding path in the target repo — for regular files, byte-identical to the scaffold source;
for `AGENTS.md`, via span-replace that preserves per-repo content (see the
`agents-md-span-replace-preserves-per-repo-sections` requirement); and for `openspec/config.yaml`, via
rules-block replace that preserves the per-repo `context:` block (see the `config-rules-block-propagates`
requirement). `AGENTS.md` and `openspec/config.yaml` are the only two files that receive partial
(non-byte-identical) handling. The script SHALL NOT inject, prepend, or append any "DO NOT EDIT" header or
other content. The script SHALL error and abort, making no changes, if the target repo path does not exist
or is not a git repository, or if a manifest-listed file is missing from the scaffold source.

#### Scenario: sync-copies-regular-file-byte-identical
- **WHEN** `sync_scaffold.py <target>` is run for a manifest-listed file that is neither `AGENTS.md` nor
  `openspec/config.yaml`
- **THEN** the file at `<target>/<path>` SHALL be byte-identical to scaffold's `<path>`

#### Scenario: sync-injects-no-header
- **WHEN** `sync_scaffold.py <target>` writes any file (regular, `AGENTS.md`, or `openspec/config.yaml`)
- **THEN** the output SHALL contain no "DO NOT EDIT — synced from openspec-scaffold" header text that the
  script added

#### Scenario: sync-handles-agents-md-via-span-replace
- **WHEN** `sync_scaffold.py <target>` processes `AGENTS.md`
- **THEN** the shared spans (the `> **MANDATORY` preamble through just before the per-repo `## Project
  context`, and `## Roles` through the end of `## After reading this file`) SHALL be replaced with
  scaffold's equivalent spans
- **AND** the target's title line, its `## Project context` section, and any tail after `## After reading
  this file` SHALL be preserved verbatim

#### Scenario: sync-handles-config-yaml-via-rules-block-replace
- **WHEN** `sync_scaffold.py <target>` processes `openspec/config.yaml`
- **THEN** the target's `rules:` block SHALL be replaced with scaffold's
- **AND** the target's `context:` block (per-repo project identity) and any other per-repo content SHALL be
  preserved verbatim

#### Scenario: sync-creates-parent-dirs
- **WHEN** a manifest-listed file's parent directory does not exist in the target repo
- **THEN** `sync_scaffold.py` SHALL create the directory before writing the file

#### Scenario: sync-aborts-on-bad-target
- **WHEN** `sync_scaffold.py` is called with a path that does not exist or has no `.git` directory
- **THEN** it SHALL exit non-zero with a clear error message and make no changes

#### Scenario: sync-aborts-on-missing-scaffold-source
- **WHEN** a path listed in the manifest does not exist in the scaffold repo at sync time
- **THEN** `sync_scaffold.py` SHALL exit non-zero with a clear error naming the missing file and SHALL make
  no changes to the target

### Requirement: check-mode-reports-drift

`scripts/sync_scaffold.py --check <target-repo-path>` SHALL report IDENTICAL / DIFFERS / MISSING for each
manifest-listed file and SHALL exit `1` if any file is not IDENTICAL, otherwise `0`. `--check` is a
diagnostic CLI, not a blocking hook, so its drift exit code is `1` (distinct from the guard's `2`). Regular
files SHALL be compared byte-for-byte against the scaffold source. `AGENTS.md` SHALL be compared by
reconstructing what it would be after a sync and comparing that to the current target, so that a per-repo
`## Project context` or tail does not register as drift. `openspec/config.yaml` SHALL likewise be compared
by its `rules:` block only, so that a per-repo `context:` block does not register as drift.

#### Scenario: check-exits-zero-on-no-drift
- **WHEN** `sync_scaffold.py --check <target>` is run and all manifest files match scaffold
- **THEN** it SHALL exit `0` and print each file as IDENTICAL

#### Scenario: check-exits-nonzero-on-drift
- **WHEN** any manifest-listed file in the target differs from scaffold or is missing
- **THEN** `sync_scaffold.py --check <target>` SHALL exit `1` and report DIFFERS or MISSING for each
  affected file

#### Scenario: check-agents-md-spans-match-despite-different-project-context
- **WHEN** `sync_scaffold.py --check <target>` processes `AGENTS.md`
- **AND** the target's `## Project context` and tail differ from scaffold's (expected — they are per-repo)
- **BUT** the shared spans are byte-identical between scaffold and target
- **THEN** the check SHALL report `AGENTS.md` as IDENTICAL and SHALL NOT exit non-zero for this file

#### Scenario: check-config-yaml-rules-match-despite-different-context
- **WHEN** `sync_scaffold.py --check <target>` processes `openspec/config.yaml`
- **AND** the target's `context:` block differs from scaffold's (expected — it is per-repo)
- **BUT** the `rules:` block is identical between scaffold and target
- **THEN** the check SHALL report `openspec/config.yaml` as IDENTICAL and SHALL NOT exit non-zero for this
  file

## ADDED Requirements

### Requirement: config-rules-block-propagates

`scripts/sync_scaffold.py` SHALL propagate the `rules:` block of `openspec/config.yaml` from the scaffold
to each downstream repo — replacing the downstream repo's `rules:` block with the scaffold's — while
preserving the downstream repo's `context:` block (the per-repo project identity) and any other per-repo
content in that file verbatim. This is the mechanism by which shared rule families (e.g. `rules.research`)
reach downstream repos instead of being hand-maintained per repo. `openspec/config.yaml` is listed in the
manifest and is one of the two partial-sync files (with `AGENTS.md`); the partial behavior described here
takes precedence over the byte-identical-copy behavior of `sync-script-copies-files` for this file. The
propagation SHALL be idempotent and SHALL be reported by the sync check mode when the downstream `rules:`
block drifts from scaffold's.

#### Scenario: rules-block-replaced
- **WHEN** `sync_scaffold.py <target>` runs and the target's `openspec/config.yaml` `rules:` block differs
  from scaffold's
- **THEN** the target's `rules:` block SHALL be replaced with scaffold's

#### Scenario: context-block-preserved
- **WHEN** `sync_scaffold.py <target>` propagates the `rules:` block to a downstream repo
- **THEN** the target's `openspec/config.yaml` `context:` block SHALL be byte-identical before and after the
  sync

#### Scenario: config-rules-propagation-idempotent
- **WHEN** `sync_scaffold.py <target>` is run twice in succession against the same target
- **THEN** the second run SHALL leave the target's `openspec/config.yaml` unchanged

#### Scenario: config-rules-drift-detectable
- **WHEN** the target's `openspec/config.yaml` `rules:` block differs from scaffold's
- **THEN** `sync_scaffold.py --check <target>` SHALL report drift and exit non-zero for it
