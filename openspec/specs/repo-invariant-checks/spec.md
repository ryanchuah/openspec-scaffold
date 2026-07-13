## Purpose

Provide the cheap enforcement slot the closure ratchet depends on: a per-repo, flat-dir,
one-file-one-invariant framework for code/repo-shape detectors (`checks/*.py`, the
sibling of `data_lint.py`'s `checks/*.sql`), executed by a stdlib-only runner registered
in the shared checks engine — so converting a found bug class into a permanent detector
costs one dropped file, not a design session.

## Requirements

### Requirement: one-dropped-file-registers-a-code-shape-invariant

The scaffold SHALL ship a stdlib-only runner (`scripts/repo_lint.py`) that executes
per-repo code/repo-shape invariants discovered via a flat `checks/*.py` glob (no
recursion, sorted filename order — the sibling of `data_lint.py`'s `checks/*.sql`
convention, sharing the same directory with disjoint extensions). Each check file is one
standalone script implementing one invariant: invoked as `<python> <file> <repo-root>` in
a subprocess, it prints a JSON array of findings `[{"path", "line", "message"}]` to
stdout (empty array = pass) and exits 0.

#### Scenario: dropped file runs on the next audit pass

- **WHEN** a repo adds a single `checks/<name>.py` conforming to the contract
- **THEN** the next runner invocation discovers and executes it with no other
  registration step

#### Scenario: violating code produces findings and gate exit

- **WHEN** a check's scan finds offending sites
- **THEN** the runner records them (count + capped sample) in its JSON artifact and exits
  2

### Requirement: runner-fails-loud-and-is-time-bounded

The runner SHALL treat any check that exits nonzero, prints unparseable stdout, or
exceeds the per-check subprocess timeout (default 120s, `--timeout` override) as an
infrastructure failure: it stops immediately at the FIRST such failure (no later sorted
check runs) and exits 3. A missing or empty `checks/` directory (no `*.py`) is not an
error: the runner reports "no checks configured" and exits 0. Exit codes are 0 clean / 2
findings / 3 infra — byte-consistent with `data_lint.py`.

#### Scenario: broken check never silently skipped

- **WHEN** a check file crashes or emits non-JSON
- **THEN** the run aborts at that check with exit 3 and names it, and subsequent check
  files are not executed

#### Scenario: hung check cannot hang the run

- **WHEN** a check exceeds the timeout
- **THEN** its subprocess is killed and the run treats it as an infra failure (exit 3)

### Requirement: runner-registers-as-a-delegating-check

`scripts/checks.py` SHALL register `repo-lint` as a floor-tier, check-family delegating
entry, auto-enabled when `checks/*.py` exists (trigger-based, like `data-lint`'s
`checks/*.sql` trigger) and overridable via `[checks.repo-lint] enabled`. Invocation
follows the data-lint integration pattern: `checks.py` calls `repo_lint.main()`
in-process with `--json` and `--checks-dir` (first `paths` entry; a second entry is an
explicit INFRA-FAIL config error) and reads the resulting JSON artifact; the runner's
findings are NOT merged into the aggregate `findings.json`.

#### Scenario: auto-detection without config

- **WHEN** a repo with no `checks.toml` contains `checks/*.py`
- **THEN** `checks.py --list` shows `repo-lint` enabled and `--floor`/`--report` run it

#### Scenario: explicit disable respected

- **WHEN** `checks.toml` sets `[checks.repo-lint] enabled = false`
- **THEN** the runner does not execute in `--floor`/`--report`, and `--list` shows it
  disabled

### Requirement: invariants-are-check-only-and-repo-trusted

Check files SHALL be treated as repo-trusted code with a documented check-only
obligation: the runner and its conventions text state that a check must never write to
the repo or any external system (the D3 caveat verbatim: keeping a custom check
check-only is the configuring repo's responsibility — the runner cannot enforce it for
arbitrary code). Conventions SHALL also carry the admission bar for new invariants:
near-zero false positives and an obvious, actionable fix (the Tricorder criteria), with
noisy checks tuned or demoted to a ledger waiver, and a stated graduation path (an
external engine such as ast-grep via `[checks.custom.*]`) if a repo outgrows bespoke
stdlib checks. Target scale is deliberate D4 scale (~5–15 invariants grown from
incidents), not a general lint suite.

#### Scenario: conventions are discoverable at the point of authoring

- **WHEN** an agent or human opens `scripts/repo_lint.py` to write a first check
- **THEN** the module docstring documents the file contract, the check-only obligation,
  the false-positive admission bar, and the graduation path — no separate handbook needed
