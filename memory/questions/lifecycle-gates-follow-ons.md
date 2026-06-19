# lifecycle-gates (W4) follow-ons

Shipped 2026-06-17. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-17-lifecycle-gates/`.

- **C4 guard coverage is partial (LOW).** `test_executor_body_agreement.py` checks only apply-executor + archive-executor pairs; no `.claude` twin for reviewer/verifier agents today.
- **Gates reference Claude-only harness skills (MED).** Simplicity gate (`simplify`/`/code-review`) and security gate (`security-review`) reference Claude-only skills; concrete OpenCode checklists are the durable floor.
- **SMALL is now formally exempt from verify gate (MED).** Monitor that risky SMALL changes aren't under-verified.
- **Scaffold-only; propagation is W6 (HIGH)** — DONE via W6 (2026-06-17).
