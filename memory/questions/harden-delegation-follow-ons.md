# harden-delegation follow-ons

Shipped 2026-06-16. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-16-harden-delegation/`.

- **[RESOLVED 2026-06-16 — W0 smoke] Commit-test-gate hook wiring live-verified.** Resolution + evidence in decisions registry (commit-gate-hook-verified-w0). Non-obvious gotcha: smoke must run from a session whose PROJECT ROOT carries the hook. Carry-forwards: A5 RESOLVED by W3; E5 RESOLVED by W5.
- **Monitor rule (a) threshold** — convergence helper stops after second same-signature observation. Monitor on real applies; loosen if too eager.
- **OpenCode-side gate plugin (v2) still deferred** — OpenCode-driven commits NOT gated. Recorded in design Non-Goals.
- **Reviewer incremental-emission quality** — observe first few real reviews after this change; revert prompt nudge if any review drops to zero findings.
- **Propagation to extrends + psc-monitor** — DONE via W6 (2026-06-17).
