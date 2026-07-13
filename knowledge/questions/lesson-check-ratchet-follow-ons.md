# lesson-check-ratchet follow-ons

Parked follow-ons from the lesson-check-ratchet change (archived
`openspec/changes/archive/2026-07-13-lesson-check-ratchet/`). None are blocking; all are
deferred, decided-elsewhere, or operator-gated.

## `outstanding.py` surfacing `open:` ratchet entries

Design deferral (design.md Open Questions): whether `scripts/outstanding.py`'s snapshot
should also surface `open:` (enforcement-deferred) ratchet-log entries alongside its other
sources. Deliberately deferred until there is real usage to learn from — the existing 30-day
lint age-flag (`ratchet_open_max_age_days`) already catches rot in the meantime, so nothing
is silently lost by waiting.

## OW-1 test-quality detector packaging

Design deferral (design.md Open Questions): whether OW-1's generic test-quality detectors
ship as `checks/*.py` tenants of the new invariant framework, or as a scaffold built-in. Not
decided here by design — OW-1 makes this call when it is actually built.

## Downstream propagation of OW-2's scaffold changes (operator-gated)

This change adds scaffold-managed files (`scripts/repo_lint.py`, `scripts/test_repo_lint.py`
→ manifest), an `AGENTS.md` synced-span bullet, and `knowledge_lint.py` ratchet enforcement —
all propagate on the next authorized `sync_scaffold.py` run, arriving **inert** downstream (no
`checks/*.py` and no per-repo ledger → auto-disabled, lint-guarded). Per-repo adoption
(naming first invariants, bootstrapping a downstream `ratchet-log.md`) is separate downstream
SMALL work, per D7 (scaffold ships the framework; each repo wires its own invariants).

Named adoption seeds (documentation only, not wiring — from design.md D6):
- **psc-monitor:** SCALE-1 (unbounded fetch), TXN-1 (autocommit test fixture)
- **extrends:** OPS-2 (fail-soft status key unread by `run_health`), MEAS-1
  (load-failure→empty-collection overwrite shape)
