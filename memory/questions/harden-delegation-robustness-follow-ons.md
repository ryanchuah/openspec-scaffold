# harden-delegation-robustness follow-ons

Shipped 2026-06-16. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-16-harden-delegation-robustness/`.

- **Propagation backlog (HIGH)** — DONE via W6 (2026-06-17).
- **Live hook-wiring smoke** — RESOLVED 2026-06-16 (W0). See decisions registry (commit-gate-hook-verified-w0).
- **`question: deny` deferred** — stdin close neutralizes it generically; adopt later if hang observed.
- **Optional bash destructive-command denylist** — defense-in-depth; deferred unless operator wants it.
- **`doom_loop` left at default `ask`** — neutralized by stdin close; monitor.
- **Canary trigger is a/b/c, not fixed `a`** — deliberate; pytest re-renders failure signature as impl changes.
