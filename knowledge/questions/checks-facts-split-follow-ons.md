# checks-facts-split follow-ons

Parked from `openspec/changes/archive/2026-07-03-checks-facts-split/notes.md` (verify-outcome
fields 4–5). All cosmetic or low-priority; none block current work.

- **facts.py radon-absent UX:** the summary line reads "INFRA-FAIL" (from the runner's FileNotFound
  record) even though the process still exits 0 by contract — consider a "skipped"-style label for
  fact-family degradation in a future pass, so the label doesn't read as a failure it isn't.
- **Preflight-aborted run writes `run-manifest.json` but not `findings.json`** (the old mid-run-abort
  path used to write both). Nothing consumes `findings.json` from aborted runs today, so this is
  latent, not active — revisit if any downstream tooling starts assuming `findings.json` always
  exists after a run.
- **Registry `trigger` strings for jscpd/vulture** read "always (enabled explicitly)" — accurate for
  config-enabled heavy checks, but slightly odd phrasing in a user-facing message; reword in a future
  pass.
- **Custom-check disable hint is imprecise for customs:** the INFRA-FAIL message's disable hint says
  `[checks.<name>] enabled = false`, but custom checks are opted in by table *presence*, not an
  `enabled` key — cosmetic inaccuracy for that one check kind.
- **Engine-refactor additions** (fold into the existing `_mode_multi` decomposition follow-on in
  `knowledge/questions/deterministic-tooling-layer-follow-ons.md`): the install-or-disable INFRA-FAIL
  message is now constructed in three places in `_mode_multi` — extract a helper; and `facts.py`'s
  `kind == "custom"` branches are unreachable dead code (customs are always check-family) — prune in
  the same pass.

See also [[commit-test-gate-hook-misfire]] (a separate bug found live during this change's apply
phase, tracked standalone since it's a delegation-harness concern, not an audit-tooling one).
