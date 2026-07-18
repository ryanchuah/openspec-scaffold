# shared-lint-gate — delta

## ADDED Requirements

### Requirement: The scaffold provisions and documents Python SAST security scanners
The scaffold SHALL additionally provision and document two Python static-analysis security
scanners — `semgrep` (SAST pattern scanning against a repo-supplied ruleset) and `bandit` (Python
security linting) — alongside the existing Go security scanners. `scripts/install-tools.sh` SHALL
install them via `pip`, guarded on pip availability, and `knowledge/reference/security-scanners.md`
SHALL document both tools, their pip provisioning, that they are version-recorded-not-gated by
`checks.py`, and that they are opt-in (default-disabled) per repo. Unlike the Go scanners, the
Python scanners are installed unpinned (latest); a repo needing version-exactness pins them in its
own dev extras.

#### Scenario: the helper provisions the Python scanners when pip is present
- **WHEN** `scripts/install-tools.sh` runs on a machine with `python3 -m pip` available
- **THEN** it SHALL `pip install` `semgrep` and `bandit` and exit `0`

#### Scenario: the helper degrades without pip
- **WHEN** `scripts/install-tools.sh` runs on a machine with no `python3 -m pip` available
- **THEN** it SHALL warn on stderr, point to `knowledge/reference/security-scanners.md`, and continue without hard-failing on the missing tool, mirroring its Go-toolchain degrade-don't-block posture

#### Scenario: the Go and Python provisioning paths are independent
- **WHEN** `scripts/install-tools.sh` runs on a machine that has pip but no Go toolchain
- **THEN** the absent Go toolchain SHALL NOT short-circuit the script, and it SHALL still provision the Python scanners and exit `0`

#### Scenario: provisioning is documented
- **WHEN** an operator provisions the scanners for a repo
- **THEN** `knowledge/reference/security-scanners.md` SHALL name `semgrep` and `bandit`, their pip provisioning path, and that they are default-disabled opt-in checks (with `semgrep` requiring a `--config <ruleset>` supplied via `[checks.semgrep] args`)

### Requirement: checks.py registers the Python SAST scanners as default-disabled built-in checks
`scripts/checks.py` SHALL register `semgrep` and `bandit` each as a heavy-tier, check-family,
built-in parsed check that is **default-disabled** (enabled only via an explicit `[checks.<name>]
enabled = true` in `checks.toml`, or a `--report --include <name>` for a single run), so that a
fresh `sync_scaffold.py` propagation SHALL NOT run them or red any gate until a repo opts in. When
enabled and run, each SHALL parse its tool's JSON output into the scaffold's normalized
`{check, rule, path, line, message}` finding shape merged into the run's aggregate `findings.json`.
The tools' probed versions SHALL be recorded but SHALL NOT gate on a version mismatch (they are
absent from `EXPECTED_TOOL_VERSIONS`, the same posture as `ruff`/`deptry`/`radon`/`vulture`).

#### Scenario: the SAST checks are registered but default-disabled
- **WHEN** `scripts/checks.py --list` runs in a repo with no `checks.toml` override
- **THEN** `bandit` and `semgrep` SHALL each appear as a registered heavy-tier check-family entry with status `disabled`

#### Scenario: an enabled SAST check normalizes findings
- **WHEN** a repo enables `bandit` or `semgrep` and the tool reports findings
- **THEN** `scripts/checks.py` SHALL normalize the tool's JSON into `{check, rule, path, line, message}` findings and include them in the run's aggregate `findings.json`

#### Scenario: SAST tool version is recorded but never gates
- **WHEN** an enabled `bandit` or `semgrep` reports a version that differs from any local expectation
- **THEN** the run SHALL record the probed version but SHALL NOT INFRA-FAIL on a version mismatch
