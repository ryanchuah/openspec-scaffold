## ADDED Requirements

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
