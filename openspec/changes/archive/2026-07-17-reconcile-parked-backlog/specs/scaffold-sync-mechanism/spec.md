## ADDED Requirements

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
