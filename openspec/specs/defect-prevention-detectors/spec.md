## Purpose

Make two recurring defect classes — forced-green/tautological tests that pass while the behavior is broken, and unbounded `fetchall()` materialization — catchable by a universal, scaffold-owned detector that ships to every repo. This capability registers two findings-capable in-process AST builtins in `scripts/checks.py` (`test-quality` and `data-scale`), distinct from the per-repo `repo-invariant-checks` framework (which is for repo-specific invariants grown from incidents).

## Requirements

### Requirement: The scaffold ships universal test-quality and data-scale detectors as in-process checks.py builtins
The scaffold SHALL register two findings-capable detectors — `test-quality` and `data-scale` — as first-class in-process builtins in `scripts/checks.py` (`family="check"`, floor tier), each performing its own AST analysis in-process with no external tool. Because they need no external binary, they SHALL be special-cased in the availability check (always available, like `inventory`) so preflight never fails on their account, and they SHALL be enabled by default (added to the autodetect defaults). Each detector SHALL emit the repo's normalized finding shape `{check, rule, path, line, message}` and participate in the standard `--floor`/`--report`/`--check` flows and the `[checks.<name>].enabled` config override. As checks-family detectors their findings surface in the audit report and set the audit exit code; they do NOT run in, or fail, the `check.sh` green gate.

#### Scenario: Both detectors are discoverable and enabled by default
- **WHEN** `checks.py --list` runs in a repo with no `checks.toml`
- **THEN** `test-quality` and `data-scale` both appear as enabled, floor-tier, check-family entries
- **AND** they are available without any external tool being installed

#### Scenario: A repo can disable a detector
- **WHEN** `checks.toml` sets `[checks.test-quality] enabled = false`
- **THEN** the detector does not run in `--floor`/`--report` and `--list` shows it disabled

### Requirement: The test-quality detector scans only test files and flags forced-green and non-deterministic test smells
The `test-quality` detector SHALL analyze only test files (`test_*.py` / `*_test.py`, matching pytest discovery) and SHALL NOT report findings on non-test source. It SHALL flag, each under a stable `rule` slug: a bare `assert True` (`assert-true`), an `assert <expr> or True` / `assert True or <expr>` forced-green assertion (`assert-or-true`), a `def test_*` whose body is only `pass` and/or a docstring (`empty-test`), a raw wall-clock call (`datetime.now`/`datetime.utcnow`/`time.time`/`time.monotonic`) inside a test function (`unfrozen-clock`), and a `patch`/`patch.object`/`mock.patch` whose target's root module equals the module-under-test derived from the filename (`self-mock`, conservatively skipped when no clear module-under-test). The detector SHALL hold to the near-zero-false-positive admission bar for these high-confidence rules; a lower-precision `discarded-return-flag` rule (a `<name>, _ = <call>()` tuple-unpack in a test that drops a returned status) MAY be included as an advisory rule with its false-positive tradeoff documented, since findings are audit-triaged rather than a CI gate.

#### Scenario: A forced-green assertion in a test file is flagged
- **WHEN** a `test_*.py` file contains `assert result or True`
- **THEN** the detector emits a finding with `rule: "assert-or-true"` at that line

#### Scenario: Non-test source is not scanned
- **WHEN** a non-test module contains `assert x or True` or a `datetime.now()` call
- **THEN** the `test-quality` detector emits no finding for it

### Requirement: The data-scale detector flags unbounded materialization on non-test source
The `data-scale` detector SHALL analyze non-test source (excluding the test-file globs and fixture directories) and SHALL flag a `.fetchall()` call (`rule: "unbounded-fetchall"`) as an unbounded result-set materialization, with a message directing the author to record an at-scale run or a bounded-domain argument in `notes.md`, or to bound the query (LIMIT/pagination). It SHALL NOT scan test files (intentional `fetchall()` in fixtures/tests is not a production hazard).

#### Scenario: An unbounded fetchall in source is flagged
- **WHEN** a non-test module contains `rows = cursor.fetchall()`
- **THEN** the detector emits a finding with `rule: "unbounded-fetchall"` at that line

#### Scenario: fetchall in a test file is not flagged
- **WHEN** a `test_*.py` fixture contains `.fetchall()`
- **THEN** the `data-scale` detector emits no finding for it

### Requirement: The scaffold ships a spec-delta-structure detector for pre-archive change deltas
The scaffold SHALL register a `spec-delta-structure` detector as a first-class in-process `checks.py` builtin (`family="check"`, floor tier, always-available, enabled by default — the same registration shape as `test-quality` and `data-scale`), because `openspec validate` is `proposal.md`-gated and therefore blind to MEDIUM changes' spec deltas. The detector SHALL discover change directories by presence (`openspec/changes/*/`, excluding `archive` and any dot-prefixed path segment), glob each change's `specs/**/spec.md` delta files, and structurally validate each — emitting the repo's normalized finding shape `{check, rule, path, line, message}` for: a delta with `### Requirement:` blocks but no `## ADDED|MODIFIED|REMOVED|RENAMED Requirements` section header; an ADDED or MODIFIED requirement whose normative `SHALL`/`MUST` is not on the first physical line of its body (the exact rule `openspec validate --strict` enforces for proposal-bearing changes); and an ADDED or MODIFIED requirement with no `#### Scenario:` block. As a checks-family detector its findings surface in the audit report and set the audit exit code; they do NOT run in, or fail, the `check.sh` green gate.

#### Scenario: A MEDIUM change's malformed delta is caught before archive
- **WHEN** a change directory contains a `specs/<cap>/spec.md` delta whose requirement's SHALL is not on its first physical line
- **THEN** `checks.py --check spec-delta-structure` emits a `shall-not-first-line` finding for that requirement, even though the change has no `proposal.md` and is invisible to `openspec validate`

#### Scenario: A well-formed delta and archived changes produce no findings
- **WHEN** a change's delta has an `## ADDED|MODIFIED Requirements` header, each requirement's SHALL on its first physical line, and at least one scenario per requirement
- **THEN** the detector reports no findings for it
- **AND** delta files under `openspec/changes/archive/` are not scanned

### Requirement: The scaffold ships a notes-checkpoint-structure detector for verify-due change checkpoints
The scaffold SHALL register a `notes-checkpoint-structure` detector as a first-class in-process
`checks.py` builtin (`family="check"`, floor tier, always-available, enabled by default — the same
registration shape as `spec-delta-structure`, `test-quality`, and `data-scale`), because the five-field
`notes.md` verify-checkpoint is prose-enforced and has been shipped incomplete or absent on real changes.
The detector SHALL discover change directories by presence (`openspec/changes/*/` at the repo root,
excluding any `archive` directory and any dot-prefixed path segment — the same exclusion the
`spec-delta-structure` detector uses, which also keeps `.claude/worktrees/…` out of scope) and, for each,
determine whether the change is **verify-due**: it SHALL skip a change whose `tasks.md` is absent or
contains no checkbox line, and skip a change with any unchecked `- [ ]` box (apply incomplete); it SHALL
evaluate only a change whose `tasks.md` checkboxes are all `- [x]`. For a verify-due change the detector
SHALL emit the repo's normalized finding shape `{check, rule, path, line, message}` for: a missing
`notes.md` (`rule: notes-missing`); a `notes.md` with no heading containing (case-insensitive)
`verify checkpoint` (`rule: checkpoint-missing`); and, when the checkpoint section is present, each of the
five required fields absent from it (`rule: checkpoint-field-missing`), matched drift-tolerantly by
keyword — (1) `verdict`, (2) `live output`/`eyeball`, (3) `defect`, (4) `as-built`, (5) `forward-looking`.
The field check is presence-only; completeness of the forward-looking field remains an orchestrator
judgment. As a checks-family detector its findings surface in the audit report and set the audit exit
code; they do NOT run in, or fail, the `check.sh` green gate. The detector is **enforcing at verify
time**: the verify skill SHALL run it and resolve findings before the archive handoff.

#### Scenario: A verify-due change missing its checkpoint is flagged
- **WHEN** a non-archived change directory has a `tasks.md` whose boxes are all `- [x]` and a `notes.md`
  with no `verify checkpoint` heading
- **THEN** `checks.py --check notes-checkpoint-structure` emits a `checkpoint-missing` finding for it

#### Scenario: A missing checkpoint field is flagged
- **WHEN** a verify-due change's `notes.md` has a verify-checkpoint section but no `as-built` field
- **THEN** the detector emits a `checkpoint-field-missing` finding naming the absent field

#### Scenario: A verify-due change with no notes.md is flagged
- **WHEN** a non-archived change directory has a `tasks.md` whose boxes are all `- [x]` but no `notes.md`
- **THEN** the detector emits a `notes-missing` finding for it

#### Scenario: An in-progress or non-lifecycle change is not flagged
- **WHEN** a change's `tasks.md` has any unchecked `- [ ]` box, or has no checkbox lines, or is absent
- **THEN** the detector emits no finding for that change (verify is not due)

#### Scenario: A well-formed checkpoint and archived changes produce no findings
- **WHEN** a verify-due change's `notes.md` carries a verify-checkpoint section containing all five fields
- **THEN** the detector reports no findings for it
- **AND** change directories under `openspec/changes/archive/` are not scanned
