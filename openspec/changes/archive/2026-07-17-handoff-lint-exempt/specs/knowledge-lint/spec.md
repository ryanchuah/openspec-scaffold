## ADDED Requirements

### Requirement: The sanctioned handoff is exempt from prose-hygiene checks as a scanned source
`knowledge_lint.py` SHALL exempt the file `knowledge/HANDOFF.md` from every prose-hygiene check that evaluates its content against the current state of the tree — specifically `retired-path-token`, `broken-prose-path-citation`, `dangling-archive-pointer`, and `duplicate-content-block`. The sanctioned mid-session handoff is a forward-looking work order, not steady-state knowledge: it exists to tell the next session what to build, so it necessarily forward-references not-yet-created files, names the archive dir its in-flight change will land in, and carries quoted context forward. This mirrors the existing `knowledge/research/` content-check exclusion, whose rationale is the mirror image (period-correct historical prose legitimately cites paths that no longer exist), extended to the two additional scan sets a handoff also trips. The exemption SHALL be keyed to the exact repo-relative path `knowledge/HANDOFF.md` — not a substring match, not any handoff-named file, and not a `knowledge/` prefix — so drift in every other knowledge doc still flags. Structural and named-file checks (orphan/duplicate-filename, audit-log, ratchet-log, ledger checks) SHALL be unaffected.

This exemption is load-bearing rather than cosmetic: the live-tree gate promotes `knowledge_lint.py` to a commit gate, so without it a session that writes a handoff cannot commit it, and the only route to a green tree is to delete the handoff — defeating the handoff mechanism the `knowledge-organization` spec mandates.

#### Scenario: a handoff's forward-referencing prose is not flagged
- **WHEN** `knowledge/HANDOFF.md` exists and cites a not-yet-created path (e.g. `` `.claude/skills/pending/SKILL.md` ``), contains a retired-path token (e.g. `ai-docs/`), names a not-yet-created archive dir (e.g. `openspec/changes/archive/2026-07-18-pending/`), and quotes a ≥8-line block from another knowledge file
- **THEN** the linter SHALL report zero findings for `knowledge/HANDOFF.md`

#### Scenario: the quoted file takes no collateral duplicate finding
- **WHEN** `knowledge/HANDOFF.md` carries forward a ≥8-line quoted block from another knowledge file (e.g. `knowledge/README.md`)
- **THEN** the linter SHALL NOT report a `duplicate-content-block` finding against that quoted file on account of the handoff, since the handoff is excluded from the compared set

#### Scenario: a handoff present on the live tree keeps the gate green
- **WHEN** a `knowledge/HANDOFF.md` of the shape above is present on the live tree
- **THEN** the live-tree lint gate SHALL pass, so the handoff is committable

#### Scenario: the identical drift in a non-handoff knowledge file still flags
- **WHEN** the same broken citation, retired-path token, planned archive pointer, or duplicated block appears in any knowledge file other than `knowledge/HANDOFF.md` (e.g. `knowledge/reference/notes.md`)
- **THEN** the linter SHALL still flag it (the exemption is scoped to the sanctioned handoff path, not a blanket suppression)

#### Scenario: a handoff-named file elsewhere is exempt from neither check family
- **WHEN** a handoff-named file exists under `knowledge/` at a path other than the sanctioned one (e.g. `knowledge/session-handoff.md`) and contains a broken citation
- **THEN** the linter SHALL flag it under the handoff-named-file check AND SHALL still flag its broken citation (the prose-hygiene exemption keys on the exact path `knowledge/HANDOFF.md`, so it does not extend to other handoff-named files)
- **AND** a handoff-named file outside `knowledge/` (e.g. `plans/session-handoff.md`) SHALL still be flagged by the handoff-named-file check, which walks the whole tree; its prose is not citation-checked there because `broken-prose-path-citation` scans only `knowledge/**/*.md` by design — a pre-existing scan-domain boundary unrelated to this exemption
