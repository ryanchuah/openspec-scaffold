# delegation-wrapper-telemetry follow-ons (OW-7, shipped 2026-07-13)

## Scheduled evidence-gated decisions (ledger consumers)

The telemetry ledger (`output/delegation-log.jsonl`) feeds two decisions the workflow audit
scheduled:

1. **Premise-gate downgrade at ~50 cumulative reviews** — currently deepseek-v4-pro for every
   premise review (propose + direction gate). If ≥50 premise reviews show fallback ≤ a
   threshold, the default may be downgraded to flash, with pro reserved for DISSENT override.
   The ledger provides the data to evaluate this — it is not yet evaluated.

2. **MEDIUM pro-pass downgrade at ~20 verifies** — currently deepseek-v4-pro for the MEDIUM
   behavioral verifier pass. If ≥20 verifies show the pass never catches defects the
   orchestrator self-review missed, the default may be downgraded to flash, with pro reserved
   for DISSENT override. Again, the ledger collects the data; evaluation is deferred.

Both decisions are evidence-gated and **not yet scheduled** — this change only produces the
data source. The evaluation itself is a future OpenSpec change (operator-initiated, not an
automatic trigger). Reference:
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md` §"how many verify reviewers do we
really need?"

## duration_s is best-effort

The ledger field `duration_s` is probed from the real opencode `part.time = {start, end}`
(epoch-ms) shape, confirmed from live output during verify. It is best-effort — any parse
issue returns `None` silently. No site captures duration today; the launcher owns wall-clock
and the ingest wrapper runs after. The load-bearing fields are
phase/agent/model/change/exit/fallback/status/verdict/retry. If duration collection matters
for the scheduled decisions, a follow-on could add a launcher-side clock or a more precise
probe, but this is low priority.
