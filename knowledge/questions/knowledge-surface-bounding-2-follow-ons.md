# knowledge-surface-bounding-2 follow-ons (OW-13, shipped 2026-07-14)

Deferred items surfaced by the change; see `knowledge/decisions/INDEX.md` (`knowledge-surface-bounding-2`)
for the shipped decision. None of these gate other work.

1. **OW-13(b) — decisions/INDEX.md year-split.** DEFERRED. `decisions/INDEX.md` is now the single
   largest boot-surface contributor (~27KB of the ~73KB total boot surface); `boot_surface_lint` will
   WARN as the aggregate keeps growing, and a year-split (`decisions/INDEX-2026.md`-style) is the
   eventual pressure-relief. No-op on the scaffold today (all entries are 2026, so there is nothing to
   split yet) — revisit once the file's growth actually pushes the aggregate toward the WARN threshold.

2. **Budget/threshold tuning.** The `status_lint.py` `EXEMPT_HEADING_BUDGETS` word budgets
   (current state 500 / immediate next action 550 / done 300 / pointers 200) and
   `boot_surface_lint.py`'s WARN/FAIL byte thresholds (80,000 / 100,000) are round-number judgment
   calls, not derived from a formula. Revisit them (one-line constant edits in each script) if
   downstream repos generate noise that suggests the numbers are miscalibrated in either direction.

3. **boot_surface_lint WARN tier is pytest-advisory-only.** The live-tree gate only asserts the FAIL
   threshold is not crossed (`boot_surface_lint.main([REPO_ROOT]) != 2`), so a WARN-band result does
   not redden the test suite and is only visible via a standalone script run. Consider wiring
   `boot_surface_lint` into `run-audit`'s reported surface so a WARN becomes visible without an
   operator manually invoking the script.

(OW-13(d) plans/-count lint is tracked separately in `plans/plans-scope-alignment.md` /
`knowledge/questions/INDEX.md` Parked — not duplicated here.)
