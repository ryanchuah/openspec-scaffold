# split-outstanding-work-skills follow-ons (shipped 2026-07-16)

Full decision + verify context: `knowledge/decisions/INDEX.md` (`outstanding-work-skill-split`,
`outstanding-work-deep-sweep-new-capability`); `knowledge/STATUS.md`. Archive:
`openspec/changes/archive/2026-07-16-split-outstanding-work-skills/`.

- **`freeze_check.py` bold-`**`-tolerance follow-on** (non-blocking). During this change's propose
  reviews the flash reviewer bold-wrapped `**VERDICT:**` / `**PREMISE:**` on 3 of 4 artifacts, which
  `freeze_check.py`'s anchored regex rejects as `missing-verdict` (false negative; each instance was
  overruled with recorded rationale at the time). `freeze_check` should tolerate optional `**`
  emphasis around the `VERDICT`/`PREMISE` tokens so this stops false-negativing on every reviewer
  that bolds its verdict line. Low priority — workaround (manual overrule) is cheap and already
  exercised successfully.

- **Downstream propagation pending** (tracked, not a blocker here). Syncing this change (new
  `outstanding-work-scan` + `outstanding-work-deep-sweep` skills; tombstone deletes the old
  `outstanding-work-review/` dir) to psc-monitor + extrends is operator-gated. Confirmed via
  read-only `sync_scaffold.py --check`: psc-monitor is MISSING both new skills and STALE on the old
  dir. Queued on `knowledge/reference/pending-downstream-propagation.md` — see that file for the
  authoritative frontier state.

- **Observation, not this change's work:** the shipped SMALL change
  `openspec/changes/knowledge-lint-gitignored-citation-exempt/` still has an unarchived lingering
  `plan.md` (with the allowlisted period-correct old-skill-name reference at its line ~53, which is
  deliberately preserved per that change's own allowlist note). Cleanup of the unarchived plan is a
  separate matter for the operator; noted only so it isn't lost.
