# verify-multimodel-gate follow-ons

Shipped 2026-06-16. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-16-verify-multimodel-gate/`.

- **Rerun-failed-and-after residual risk (monitored)** — fix for a late pass not re-checked by earlier passes; accepted trade-off.
- **OpenCode Task-tool verifier path not live-probed** — confirmed by design; probe when next on OpenCode.
- **V6(d) edit-denial not separately probed** — low risk (`edit: deny` is structurally present).
- **Bash destructive-command denylist deferred** — defense-in-depth; deferred unless operator wants it.
- **Scaffold has no runnable test suite** — by design (no `scripts/test-cmd`).
- **Propagation backlog (HIGH)** — DONE via W6 (2026-06-17).
