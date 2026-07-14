## ADDED Requirements

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
