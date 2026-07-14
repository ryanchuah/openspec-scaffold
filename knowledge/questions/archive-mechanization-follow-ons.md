# archive-mechanization follow-ons (OW-12, shipped 2026-07-14)

Full decision → `knowledge/decisions/INDEX.md` (`archive-mechanization`). Full evidence → the
archived change's `notes.md`
(`openspec/changes/archive/2026-07-14-archive-mechanization/notes.md`).

## (a) Unify the `plan_spec` None-branch and else-branch ADDED-collision logic (low priority)

The new-main-spec-creation path (`main_spec is None`) and the existing-main-spec path each carry
their own ADDED-collision check — roughly 15 duplicated lines. Deferred to avoid churning
just-fixed code (this logic was the source of one of the 3 adversarial-fixture defects); unify if
the file is next touched.

## (b) Headerless-requirement parse (low priority, latent)

A main spec with a `### Requirement:` block before any `## Requirements` header parses oddly. No
repo spec triggers this today (openspec always emits `## Requirements`). Monitor; not a live bug.

## (c) RENAMED true debut (monitored)

RENAMED promotion is now mechanized under a tested contract with adversarial fixtures, but the
first REAL archive carrying a RENAMED delta is still its live debut in production use. Watch the
first such archive closely.

## (d) REMOVED-absent silent-skip (monitored, design D4 decision)

A REMOVED operation naming an already-absent requirement is a reported skip, not an anomaly
(idempotency-preserving; design D4). Flip to anomaly only if a typo'd REMOVED name is ever observed
silently no-op'ing in practice.

## (e) pro-verifier no-output was not persistent (info)

The prior change's HANDOFF noted a zero-output pro-tier verifier pass; this change's pro behavioral
pass emitted a normal READY verdict. The earlier degradation does not appear to be persistent — kept
as a watch item, not a blocker.
