## ADDED Requirements

### Requirement: archive-step-flags-wider-knowledge-drift

The archive step SHALL also detect drift in the **wider** knowledge bodies that the existing
three-tracker reconciliation (`knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`,
`knowledge/questions/`) does not cover. Specifically, at archive the archive step SHALL (a) run the
deterministic `scripts/knowledge_lint.py` over the tracked knowledge tree and surface any drift it
reports, and (b) re-check the wider knowledge bodies — `knowledge/reference/` (runbooks, compliance),
`knowledge/roadmap.md`, and the `knowledge/questions/` Parked backlog (the individual
`knowledge/questions/<item>.md` bodies, not only the one-line pointers in `questions/INDEX.md`) — for
claims about the just-shipped change that the change has now made stale (e.g. a feature this change
shipped that a reference doc still calls "not yet built"). This wider sweep SHALL be **flag-only**: the archive step
SHALL surface findings for operator/primary follow-up and SHALL NOT auto-rewrite the wider bodies.
Correcting per-repo prose content remains separate manual follow-on work. The existing three-tracker
reconciliation behaviour (which writes) is unchanged; this requirement is additive.

#### Scenario: archive-runs-deterministic-linter
- **WHEN** a change is archived
- **THEN** the archive step SHALL run `scripts/knowledge_lint.py` over the knowledge tree and report any drift findings it produces
- **AND** those findings SHALL be surfaced (not swallowed) but SHALL NOT block archive completion — pre-existing drift unrelated to the current change must not halt the archive (flag-only)

#### Scenario: archive-flags-now-stale-claims-about-shipped-change
- **WHEN** a change ships a feature that a wider knowledge body (`knowledge/reference/`, `knowledge/roadmap.md`, or the `knowledge/questions/` Parked backlog) still describes as "not yet built" / planned
- **THEN** the archive step SHALL flag that now-stale claim for operator/primary follow-up

#### Scenario: wider-sweep-is-flag-only
- **WHEN** the archive step performs the wider-body re-check and finds stale claims
- **THEN** it SHALL NOT auto-edit those bodies (flag-only); only the three trackers are reconciled and written, as before
