## ADDED Requirements

### Requirement: A shared ruff config defines lint and format for every repo
The scaffold SHALL ship a single scaffold-managed `ruff.toml` at the repo root (NOT a
`pyproject.toml` — the scaffold has none, and downstream pyprojects stay lint-config-free because
ruff prefers `ruff.toml`). It SHALL select the rule families **E, F, I, B** and SHALL enforce
`ruff format`. Any per-file-ignores SHALL live in this one shared file; paths that a downstream repo
does not have are harmless, so one file serves every repo.

#### Scenario: ruff reads the shared config
- **WHEN** `ruff check` runs in a repo carrying the scaffold `ruff.toml`
- **THEN** it applies exactly the E, F, I, B selection from that file, not ruff's unconfigured default ruleset

#### Scenario: format is enforced, not advisory
- **WHEN** `ruff format --check` runs on a tree that is not formatter-clean
- **THEN** it SHALL exit non-zero (format drift is a gate failure, not a warning)

### Requirement: check.sh is the single definition of green
The scaffold SHALL ship a scaffold-managed `scripts/check.sh` that runs, in order, `ruff check`,
`ruff format --check`, and the repo's tests via `scripts/test-cmd`, exiting non-zero if any stage
fails and zero only when all pass. `check.sh` SHALL be the one script that the Claude commit hook,
CI, and humans all invoke, so "green" has exactly one definition per repo. Its exit convention SHALL
be documented in `knowledge/reference/exit-codes.md`.

#### Scenario: any present-tool violation fails the gate
- **WHEN** a lint violation, a format drift, OR a failing test is produced by a tool that is present
- **THEN** `check.sh` SHALL exit non-zero, naming the stage that failed

#### Scenario: an all-clean tree is green
- **WHEN** lint, format, and tests all pass
- **THEN** `check.sh` SHALL exit `0`

#### Scenario: a missing lint/format tool is a config error, not a block
- **WHEN** `ruff` is not installed/resolvable in the environment running `check.sh`
- **THEN** `check.sh` SHALL warn on stderr, skip the lint and format stages, and continue — it SHALL NOT hard-block the commit on absent tooling (mirroring `test-gate.sh`'s existing unresolvable-executable branch); provisioning the tools everywhere is the job of `install-tools.sh` + dev extras + CI, not the local hook

#### Scenario: tests delegate to the per-repo command
- **WHEN** `check.sh` reaches the test stage
- **THEN** it SHALL run the repo's `scripts/test-cmd` (not a hard-coded command); when `scripts/test-cmd` is absent the test stage is a no-op while lint and format still run

### Requirement: The doc-lints are enforced on the live tree
The pytest suite SHALL include tests that run `knowledge_lint.py` and `status_lint.py` against the
**real repository tree** (mirroring the existing `scaffold_lint.py` live-tree test), so that doc
drift turns the suite red and is therefore blocked by the commit gate. This converts the doc-lints
from memory-invoked tooling to gate-enforced invariants without changing their detection logic.

#### Scenario: live-tree doc drift fails the suite
- **WHEN** a knowledge doc is given a drift finding the linter detects (e.g. a genuinely-broken citation) and the suite runs
- **THEN** the live-tree doc-lint test SHALL fail, so the commit gate blocks the commit

#### Scenario: a clean tree passes
- **WHEN** the knowledge tree has no drift findings
- **THEN** the live-tree doc-lint tests SHALL pass

### Requirement: install-tools.sh provisions pinned security scanners
The scaffold SHALL ship a scaffold-managed `scripts/install-tools.sh` that installs pinned versions
of the security scanners `gitleaks` and `osv-scanner` (with `deptry` provided via dev extras rather
than a binary install). It SHALL be idempotent (safe to re-run) and its use SHALL be documented in
`knowledge/reference/new-repo-bootstrap.md`. C ships this provisioning mechanism; per-repo CI
enforcement of the scanners is downstream wiring (D1/D2), not part of this capability.

#### Scenario: install provisions the pinned scanners
- **WHEN** `scripts/install-tools.sh` runs on a machine without the scanners
- **THEN** it installs the pinned `gitleaks` and `osv-scanner` versions and exits `0`

#### Scenario: re-running is idempotent
- **WHEN** `scripts/install-tools.sh` runs again with the scanners already present at the pinned versions
- **THEN** it SHALL NOT error and SHALL leave the environment unchanged

### Requirement: The apply executor autofixes touched files before reporting done
The apply phase SHALL run `ruff check --fix` and `ruff format` on the files it touched before
reporting a task done, so implementation work lands formatter-clean and lint-clean. This instruction
SHALL appear in the apply SKILL and in BOTH executor agent bodies —
`.claude/agents/apply-executor.md` and `.opencode/agents/apply-executor.md` — with those two bodies
byte-identical (guarded by `scripts/test_executor_body_agreement.py`).

#### Scenario: executor bodies carry the autofix line in lockstep
- **WHEN** `scripts/test_executor_body_agreement.py` byte-compares the two executor bodies
- **THEN** both SHALL contain the ruff autofix instruction and the comparison SHALL pass

### Requirement: The shared lint layer is scaffold-managed
`ruff.toml`, `scripts/check.sh`, and `scripts/install-tools.sh` SHALL be listed in
`scripts/scaffold_manifest.txt` so `sync_scaffold.py` propagates them byte-identical downstream. The
per-repo `checks.toml` SHALL NOT be a manifest entry (it stays per-repo config, per A's seed
convention).

#### Scenario: manifest lists the lint-layer files
- **WHEN** `scripts/scaffold_manifest.txt` is read
- **THEN** it SHALL contain entries for `ruff.toml`, `scripts/check.sh`, and `scripts/install-tools.sh`

#### Scenario: per-repo config stays unmanaged
- **WHEN** the manifest is checked for `checks.toml`
- **THEN** `checks.toml` SHALL NOT be a manifest entry
