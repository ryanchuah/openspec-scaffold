# Premise-review-gate follow-ons

## 1. Explore-altitude dissent calibration (monitor, tune after real runs)

The behavioral smoke confirmed `DISSENT` fires on a clearly-wrong direction, but the *false-positive*
side — that the mandate's D11 calibration ("dissent only when demonstrably wrong, not merely
under-specified") holds on real, thin explore briefs — has not been observed in production. Monitor
the first real explore-gate runs; if it over-fires on under-specified-but-sound briefs, tighten the
D11 wording.

## 2. Slug↔change-name relocation risk (monitored)

If the operator explores under one topic slug but runs `propose` under a different name, the brief is
not relocated and is orphaned in `plans/<slug>/`. Monitored risk; a future hardening could surface a
warning when a `plans/*/explore-brief.md` exists but no slug matched at propose.

## 3. Minor cosmetic follow-ons

(a) explore `SKILL.md` step 2 says "(All-Altitudes, see design)" where it means "Altitude 1 direction
gate". (b) propose `SKILL.md` step 2 picked up a 1-space list-marker indentation drift (renders fine).

## 4. Downstream scaffold propagation

`AGENTS.md` + the four skill/agent files are scaffold-managed; after this commits, run
`scripts/sync_scaffold.py <downstream-repo>` per downstream repo to propagate, then review and commit
there. Not a code item — a rollout action.
