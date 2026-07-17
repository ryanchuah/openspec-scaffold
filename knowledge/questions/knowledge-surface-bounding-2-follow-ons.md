# knowledge-surface-bounding-2 follow-ons (OW-13, shipped 2026-07-14)

Deferred items surfaced by the change; see `knowledge/decisions/INDEX.md` (`knowledge-surface-bounding-2`)
for the shipped decision. None of these gate other work.

1. **OW-13(b) — decisions/INDEX.md pressure relief. RESOLVED 2026-07-17.** The operator call landed
   on the pressure-triggered chronological roll (`roll-decisions-index` change — this change), which
   supersedes the year-split idea: `knowledge/decisions/INDEX.md` keeps only a byte-budgeted newest
   tail, older entries roll verbatim to `knowledge/decisions/HISTORY.md` via `scripts/roll_decisions.py`.
   Applied to this repo's own registry — INDEX.md now holds only the newest tail and the boot
   surface is back under the default WARN threshold.

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
