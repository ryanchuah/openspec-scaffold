# propagate-scaffold follow-ons (recommended, not yet built)

**Source:** the 2026-07-15 extrends propagation (and the psc-monitor sync before it). The executed
extrends propagation handoff (a plans/ doc, pruned after execution) folded its load-bearing lessons
into the `propagate-scaffold` skill, and its recommended scaffold follow-ons are captured here so
they survive the prune. Route each through the normal SMALL/MEDIUM lifecycle when picked up.

- **Wrapper stale-output hardening (from F5).** `scripts/opencode_delegate.py` should truncate its
  `<out>.text.txt` at start (or write to a run-namespaced path), or fail-loud when the source
  `.jsonl` is older than a pre-existing `.text.txt`, so a stale artifact can never masquerade as the
  current run. Also consider switching the AGENTS.md / skill wrapper invocations to the explicit
  `python3 scripts/opencode_delegate.py` form (belt-and-suspenders, independent of the exec bit).
- **isort-collision guard (from F3).** A scaffold test asserting that any scaffold test-module doing
  `import checks` (or another name colliding with a plausible downstream top-level package) after a
  `sys.path.insert` carries the `# noqa: … I001` guard — stops the per-file whack-a-mole as new test
  files land. `scripts/test_facts.py` also carries the bare guard without the rationale comment.
- **Sync summary output (from F1, low priority).** `scripts/sync_scaffold.py` runs silently (exit 0,
  no stdout); a one-line "copied N / added M / deleted K, span-merged AGENTS.md" summary would make
  the sync legible without a follow-up `git status`.
- **status_lint per-section cap in skill Step 5 (new, from the extrends sync).** The extrends
  propagation tripped `status_lint`'s hardcoded 550-word `## Immediate next action` cap on a bloated
  downstream STATUS.md — a reconciliation class the skill's Step 5 names boot_surface and
  knowledge_lint for but not status_lint. Consider adding a Step 5 bullet: condense the offending
  section info-preservingly (relocate shipped-change retrospectives to their plans/archive homes,
  keep every live item), since the cap is hardcoded (no per-repo lever like boot_surface's
  `[boot_surface_lint]` table).
