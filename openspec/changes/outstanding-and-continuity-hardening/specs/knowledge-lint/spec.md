# Delta — knowledge-lint (outstanding-and-continuity-hardening)

Corrective + widening delta: the promoted `knowledge-lint` capability pins the handoff-file
check to the **repository root** and to a case-sensitive `HANDOFF*`/`HANDOVER*` **prefix**.
Downstream repos accumulate handoff-named files in `plans/`, `tmp/`, and `knowledge/research/`
— none of which the root-only prefix check can see — so the single-canonical-handoff decision
(`knowledge-handoff-file`, 2026-07-03) is under-enforced. This delta widens the check to the
whole repo, matches `handoff`/`handover` as a case-insensitive substring, and keeps
`knowledge/HANDOFF.md` as the sole exemption. The check still rides the same live-tree gate and
still respects gitignore (ignored paths are not scanned).

## RENAMED Requirements
- FROM: `### Requirement: Root-level handoff files are flagged`
- TO: `### Requirement: Handoff-named files are flagged`

## MODIFIED Requirements

### Requirement: Handoff-named files are flagged
`knowledge_lint.py` SHALL flag any non-gitignored file anywhere in the repository whose name
contains `handoff` or `handover` (case-insensitive substring match), mechanizing the
knowledge-handoff-file decision that exactly one sanctioned handoff file may exist. The
sanctioned ephemeral `knowledge/HANDOFF.md` SHALL be the sole exemption; every other
handoff-named file — at any depth, tracked or merely present in the working tree — SHALL be
flagged. Gitignored paths SHALL NOT be scanned (consistent with the other repo-wide checks), so
transient handoff-named files under ignored directories are out of scope for this check. This
check rides the same live-tree gate as the other doc-lints.

#### Scenario: a nested handoff-named file is flagged
- **WHEN** a file whose name contains `handoff` (any case) exists at any path outside
  `knowledge/HANDOFF.md` and is not gitignored — e.g. `plans/session-handoff.md`
- **THEN** the linter SHALL flag it as a finding

#### Scenario: a handover-named file is matched case-insensitively
- **WHEN** a non-gitignored file named e.g. `docs/HANDOVER.md` or `tmp/session-Handover.md` exists
- **THEN** the linter SHALL flag it as a finding

#### Scenario: the sanctioned in-tree handoff is exempt
- **WHEN** `knowledge/HANDOFF.md` exists (the sanctioned mid-session handoff location)
- **THEN** the linter SHALL NOT flag it

#### Scenario: gitignored handoff files are not scanned
- **WHEN** a handoff-named file exists under a gitignored path — e.g. `output/x-handoff.md`
- **THEN** the linter SHALL NOT flag it
