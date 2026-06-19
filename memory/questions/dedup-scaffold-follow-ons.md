# dedup-scaffold (W2) follow-ons

Shipped 2026-06-17. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-17-dedup-scaffold/`.

- **[BUG — archive-executor omits EXIT-sentinel] (MED, pre-existing).** `openspec-archive-change` backgrounds its executor but the `opencode run` invocation does not append `; echo "EXIT=$?" > /tmp/archive-out.exit` — timeout/crash detection for archive is unreliable. One-line fix; candidate for a standalone follow-up change.
- **[Orchestration — stress slicing large changes into task ranges] (MED).** The apply skill advises "prefer splitting delegation across task ranges" but guidance is easy to miss; monolithic dispatch caused a W2 timeout. Make guidance more prominent.
- **[Tier-scale the delegation timeout budgets] (MED).** Timeout table is fixed per phase; consider scaling apply/verify budgets by change tier or task count. Currently a deliberate non-goal.
