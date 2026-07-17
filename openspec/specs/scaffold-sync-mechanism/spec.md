## Purpose

Define the behavioral requirements for the scaffold sync mechanism — the tooling and guards that keep
shared workflow files in sync between openspec-scaffold (the golden source) and downstream repos
(extrends, psc-monitor, and future repos built from scaffold) — byte-identical for regular files, and
span-identical on the shared sections for `AGENTS.md`. The mechanism injects no per-file header;
the single human-facing "scaffold-managed — edit upstream" note lives in `AGENTS.md` and as ordinary
content in the manifest.

## Requirements

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

---

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

---

### Requirement: sync-is-idempotent

Re-running the sync SHALL be safe to repeat — the mechanism's whole premise is that each future scaffold
change is propagated by re-running it. A sync over an already-synced target SHALL leave the target
unchanged, and the AGENTS.md span-replace SHALL be a fixed point on its own output.

#### Scenario: sync-twice-is-noop
- **WHEN** `sync_scaffold.py <target>` is run twice in succession against the same target
- **THEN** `sync_scaffold.py --check <target>` SHALL exit `0` after the second run
- **AND** the target files SHALL be unchanged between the first and second sync

#### Scenario: idempotent-agents-md-reconstruction
- **WHEN** the AGENTS.md span-replace is applied to its own previous output (same scaffold source)
- **THEN** the result SHALL be byte-identical to that previous output (no accreted lines)

---

### Requirement: pre-commit-guard-blocks-scaffold-managed-edit

A downstream repo's `.claude/settings.json` SHALL include a `PreToolUse` hook that runs
`scripts/scaffold_check.py`, which detects when a scaffold-managed file is staged for commit and blocks the
commit, directing the editor to change scaffold instead. The guard SHALL detect scaffold-managed files by
intersecting the manifest with `git diff --cached --name-only`, SHALL resolve the manifest relative to its
own file location (not the current working directory), and SHALL require no knowledge of scaffold's path.

#### Scenario: hook-blocks-when-manifest-file-staged
- **WHEN** `scripts/scaffold_check.py` runs in a downstream repo
- **AND** any file listed in `scripts/scaffold_manifest.txt` appears in `git diff --cached --name-only`
- **THEN** it SHALL exit `2` (the Claude Code `PreToolUse` blocking code) with a message that names the
  affected files and directs the editor to change scaffold instead

#### Scenario: hook-passes-when-no-manifest-file-staged
- **WHEN** `scripts/scaffold_check.py` runs and no scaffold-managed file is staged
- **THEN** it SHALL exit `0`

#### Scenario: override-with-no-verify
- **WHEN** an operator intentionally commits scaffold-managed changes in a downstream repo (after running
  `sync_scaffold.py` to apply a new scaffold version, or when reverse-promoting a downstream improvement
  back to scaffold) and runs `git commit --no-verify`
- **THEN** the hook SHALL be bypassed (`--no-verify` is the sanctioned escape for all intentional
  scaffold-managed file changes)

#### Scenario: guard-only-intercepts-claude-bash-commits
- **WHEN** a commit is made outside Claude Code's Bash tool (an operator terminal commit, or an
  opencode/deepseek executor commit)
- **THEN** the `PreToolUse` guard does NOT intercept it — this is a documented coverage limitation, not a
  defect; `git commit --no-verify` is the sanctioned escape for deliberate scaffold-managed edits

---

### Requirement: agents-md-span-replace-preserves-per-repo-sections

The span-replace algorithm SHALL preserve all per-repo content in `AGENTS.md` and SHALL raise an error
rather than silently corrupt the file.

#### Scenario: project-context-preserved
- **WHEN** `sync_scaffold.py` processes a downstream repo's `AGENTS.md`
- **THEN** the `## Project context` section in the output SHALL be byte-identical to that section in the
  pre-sync target file

#### Scenario: no-project-context-case
- **WHEN** the target `AGENTS.md` has no `## Project context` section (e.g. extrends)
- **THEN** the span-replace SHALL still succeed, preserving the title and replacing only the shared spans,
  inserting no empty project-context section

#### Scenario: psc-monitor-tail-preserved
- **WHEN** `sync_scaffold.py` processes psc-monitor's `AGENTS.md`
- **THEN** everything after `## After reading this file` (the `---` separator and `# Project reference`
  appendix) SHALL be preserved verbatim in the output

#### Scenario: missing-anchor-aborts
- **WHEN** the target `AGENTS.md` is missing `## Roles` or `## After reading this file`
- **THEN** `sync_scaffold.py` SHALL exit non-zero with a descriptive error and make no changes

#### Scenario: scaffold-tail-invariant-aborts
- **WHEN** scaffold's `AGENTS.md` has a tail separator (a `---` rule or a `# ` heading) after `## After
  reading this file`
- **THEN** `sync_scaffold.py` SHALL abort with a descriptive error and make no changes

#### Scenario: long-target-no-tail-aborts
- **WHEN** a target `AGENTS.md` longer than 300 lines yields no detectable tail separator after `## After
  reading this file`
- **THEN** `sync_scaffold.py` SHALL abort with a descriptive error rather than risk truncating the per-repo
  tail

---

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

### Requirement: sync-stamps-scaffold-provenance

`scripts/sync_scaffold.py <target-repo-path>` SHALL, after a successful sync, write a provenance
beacon file at the target repo root (`.scaffold-version`) recording the scaffold's current git HEAD:
its short commit SHA, that commit's own committer date (ISO-8601), and its subject line. The purpose
is to make scaffold staleness visible from *inside* the downstream repo — a downstream agent can read
the beacon to see which scaffold commit the repo was last synced from, without running `--check` from
the scaffold side.

The beacon SHALL NOT be a manifest-listed file. Because `--check` and the pre-commit guard iterate
only manifest entries, a non-manifest beacon can never cause `sync_scaffold.py --check <target>` to
report drift, and the `check-mode-reports-drift` contract is unaffected. The beacon's content SHALL
be derived solely from the scaffold HEAD commit (deterministic per commit — NOT wall-clock time), so
that two syncs run against the same target at the same scaffold HEAD write a byte-identical beacon and
the `sync-is-idempotent` contract holds. Writing the beacon SHALL be best-effort: if the scaffold HEAD
cannot be resolved (e.g. git is unavailable or the scaffold is not a git repo), the sync SHALL write a
beacon marked `unknown` and SHALL NOT abort — beacon failure never blocks propagation. The beacon is
written only by the full `sync` action, not by `--check` or `--check-refs`.

#### Scenario: sync-writes-provenance-beacon
- **WHEN** `sync_scaffold.py <target>` completes a sync and the scaffold HEAD is resolvable
- **THEN** `<target>/.scaffold-version` SHALL exist and contain the scaffold HEAD short SHA, the HEAD
  commit's committer date, and its subject line

#### Scenario: beacon-does-not-register-as-drift
- **WHEN** `sync_scaffold.py --check <target>` is run after a sync has written `.scaffold-version`
- **THEN** the check output and exit code SHALL be exactly what they would be without the beacon —
  `.scaffold-version` SHALL NOT appear in the drift report and SHALL NOT cause a non-zero exit

#### Scenario: beacon-is-idempotent-per-head
- **WHEN** `sync_scaffold.py <target>` is run twice against the same target at the same scaffold HEAD
- **THEN** `<target>/.scaffold-version` SHALL be byte-identical after the second run as after the first

#### Scenario: beacon-write-is-best-effort
- **WHEN** the scaffold HEAD cannot be resolved during a sync
- **THEN** the sync SHALL still complete (all manifest files copied) and the beacon SHALL be written
  with an `unknown` marker rather than the sync aborting or raising

### Requirement: removed-manifest-derives-skill-scan-vocabulary

`scripts/scaffold_manifest_removed.txt` (the tombstone manifest) SHALL additionally be the source of
truth for retired skill names used by `scaffold_lint.py`'s `dangling-skill-refs` check. The check SHALL
derive its non-`openspec-` scan vocabulary from the manifest's `.claude/skills/<name>/` directory
entries rather than a hand-maintained list, so a lingering reference to a removed skill is flagged and
the vocabulary cannot drift. Non-skill manifest entries (tombstoned paths that are not a
`.claude/skills/<name>/` directory) SHALL contribute no token to the vocabulary. A missing or unreadable
manifest SHALL yield an empty vocabulary rather than an error.

#### Scenario: retired skill name is flagged when referenced
- **WHEN** a retired skill name — an entry in `scaffold_manifest_removed.txt` naming a
  `.claude/skills/<name>/` directory that no longer exists on disk — is referenced in the scanned
  surface
- **THEN** the `dangling-skill-refs` check SHALL flag it

#### Scenario: a current skill name is never flagged
- **WHEN** a scanned-surface reference names a skill directory that currently exists under
  `.claude/skills/`
- **THEN** the check SHALL NOT flag it, regardless of whether the manifest also lists that name

#### Scenario: a non-skill manifest entry contributes no token
- **WHEN** `scaffold_manifest_removed.txt` contains a tombstoned entry that is not a
  `.claude/skills/<name>/` directory (e.g. `scripts/audit_bundle.py`)
- **THEN** that entry SHALL contribute no token to the scan vocabulary

#### Scenario: absent manifest lints clean
- **WHEN** `scaffold_manifest_removed.txt` is missing or unreadable
- **THEN** the derived vocabulary SHALL be empty and the check SHALL report no findings on that account,
  rather than erroring
