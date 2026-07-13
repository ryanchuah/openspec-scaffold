# Delta — defect-prevention-detectors (mechanized-verify-propose-gates)

Adds a third universal in-process detector to the capability. `openspec validate` discovers changes
via `proposal.md`, so a MEDIUM change (tasks.md-only) and its spec deltas are never CLI-validated —
a malformed delta (e.g. a normative SHALL not on the requirement's first physical line) is invisible
until it fails `openspec validate --strict` at archive, after apply has already run. This detector
makes that defect class catchable by a deterministic, scaffold-owned check that ships to every repo,
closing the ratchet item `medium-change-spec-delta-unvalidated`.

## ADDED Requirements

### Requirement: The scaffold ships a spec-delta-structure detector for pre-archive change deltas
The scaffold SHALL register a `spec-delta-structure` detector as a first-class in-process `checks.py` builtin (`family="check"`, floor tier, always-available, enabled by default — the same registration shape as `test-quality` and `data-scale`), because `openspec validate` is `proposal.md`-gated and therefore blind to MEDIUM changes' spec deltas. The detector SHALL discover change directories by presence (`openspec/changes/*/`, excluding `archive` and any dot-prefixed path segment), glob each change's `specs/**/spec.md` delta files, and structurally validate each — emitting the repo's normalized finding shape `{check, rule, path, line, message}` for: a delta with `### Requirement:` blocks but no `## ADDED|MODIFIED|REMOVED|RENAMED Requirements` section header; an ADDED or MODIFIED requirement whose normative `SHALL`/`MUST` is not on the first physical line of its body (the exact rule `openspec validate --strict` enforces for proposal-bearing changes); and an ADDED or MODIFIED requirement with no `#### Scenario:` block. As a checks-family detector its findings surface in the audit report and set the audit exit code; they do NOT run in, or fail, the `check.sh` green gate.

#### Scenario: A MEDIUM change's malformed delta is caught before archive
- **WHEN** a change directory contains a `specs/<cap>/spec.md` delta whose requirement's SHALL is not on its first physical line
- **THEN** `checks.py --check spec-delta-structure` emits a `shall-not-first-line` finding for that requirement, even though the change has no `proposal.md` and is invisible to `openspec validate`

#### Scenario: A well-formed delta and archived changes produce no findings
- **WHEN** a change's delta has an `## ADDED|MODIFIED Requirements` header, each requirement's SHALL on its first physical line, and at least one scenario per requirement
- **THEN** the detector reports no findings for it
- **AND** delta files under `openspec/changes/archive/` are not scanned
