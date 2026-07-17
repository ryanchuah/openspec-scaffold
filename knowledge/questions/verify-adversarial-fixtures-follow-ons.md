# verify-adversarial-fixtures follow-ons

Parked from `openspec/changes/archive/2026-07-14-verify-adversarial-fixtures/notes.md` (Verify
checkpoint field 5). Both items are non-blocking.

- **`lessons.md` §2 registry row (low priority):** consider adding a `rules.verify` row to the
  `knowledge/lessons.md` §2 single-source registry — its canonical home (`config.yaml`
  `rules.verify`) now governs two rules (the self-review steps and the new adversarial/boundary
  fixture obligation). Archive-time judgment call; not done inline.
- **MONITORED — verifier verdict-block adherence:** the openspec-verifier occasionally emits a
  terse prose summary instead of the mandated `## Verify Pass / VERDICT:` block (observed
  2026-07-14 during this change's own pro behavioral pass). The `opencode_delegate.py` wrapper's
  marker assertion is the working backstop — it caught the miss and a single re-run with a strict
  output-contract prompt cleared it. Candidate for a verifier-prompt hardening if this recurs.
  **Another observation (2026-07-16, `reconcile-parked-backlog`):** the pro verify pass again
  emitted a well-formed but evidence-free verdict block despite genuinely doing the work (ran
  `pytest -q`, all three linters, and read all 5 delta specs, confirmed from its own transcript).
  Still not recurring often enough to warrant the prompt hardening on its own.
