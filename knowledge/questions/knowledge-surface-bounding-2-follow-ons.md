# knowledge-surface-bounding-2 follow-ons (OW-13, shipped 2026-07-14)

Deferred items surfaced by the change; see `knowledge/decisions/INDEX.md` (`knowledge-surface-bounding-2`)
for the shipped decision. None of these gate other work.

1. **OW-13(b) — decisions/INDEX.md pressure relief. LIVE — the revisit trigger has fired, and the
   proposed remedy does not work.** Updated 2026-07-17 during `reconcile-parked-backlog`.

   *The trigger fired.* This item said "revisit once the file's growth actually pushes the aggregate
   toward the WARN threshold." It has: the boot surface sat in **WARN** before that change, dipped
   under only because its tracker sweep shaved the questions index, and **re-crossed on that change's
   own archive** — archive spent more (a STATUS section + 3 decision registry lines + new questions
   items) than the sweep saved. Net: worse than before. Sweeping `knowledge/questions/` is not
   pressure relief; the WARN band is now the steady state.

   *The remedy is a no-op.* A **year**-split (`decisions/INDEX-2026.md`) still cannot help, for the
   same reason recorded when this was filed: **every entry is 2026**. There is nothing to split. The
   original plan quietly assumed a year boundary would arrive before the pressure did. It did not.

   *So the real options are different ones, and picking among them is the actual open question:*
   - **Split by something other than year** — by half-year, or by capability/topic, with the boot-read
     rule already being "scan the entries relevant to the current task" (AGENTS.md), which a topic
     split serves better than a chronological one anyway.
   - **Attack entry verbosity, not file count.** The registry format is
     `- **YYYY-MM-DD** · <slug> · <essence> → <archive path>`, and "essence" has drifted long —
     several recent entries (this change's three included) run 300-450 chars. A terser essence with
     the detail living in the linked archive is closer to the format's intent and costs no new file.
   - **Reconsider what the boot budget counts.** `AGENTS.md` (~33KB) and `decisions/INDEX.md` (~35KB)
     are ~82% of the surface, yet `decisions/INDEX.md` is NOT a full mandatory read — AGENTS.md says
     to scan only the relevant entries. Budgeting it at full weight may be miscounting the real cost.

   Not fixed here: this is a MEDIUM standalone needing its own design, and `reconcile-parked-backlog`
   deliberately excluded it rather than expand scope post-freeze. **Operator call.**

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
