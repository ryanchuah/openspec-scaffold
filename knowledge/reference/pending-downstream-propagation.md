# Pending downstream propagation (operator-gated)

Scaffold-managed changes propagate to downstream repos (`extrends`, `psc-monitor`) via
`scripts/sync_scaffold.py` — an **operator-gated** step, typically run as a batch. This ledger
records scaffold changes that shipped **locally** (to scaffold `main`, unpushed) but are **not yet
propagated**, plus any per-change caveat that matters at propagation time. It is per-repo state (not
scaffold-managed): each repo's propagation frontier differs, so this file does not itself propagate.

## Frontier — both downstreams current as of 2026-07-15
- **extrends** — converged to scaffold HEAD (beacon `6ba66dc`), commit `1853b78` (local, unpushed).
  This sync carried the entire 2026-07-04 → 2026-07-15 backlog (wave-1/2 hardening, the audit skills,
  archive-mechanization + apply-delta/archive-move, repo-lint, boot-surface, freeze-check,
  opencode-delegate, delegation-harness single-sourcing, finding-closure-ratchet). Per-repo caveats:
  `[boot_surface_lint]` override 120K/140K in `checks.toml` (boot surface ~113.5 KB after a STATUS
  condense); the ~27 handoff-named files were renamed `*-handoff.md` → `*-notes.md`;
  `knowledge/ratchet-log.md` seeded (zero entries). Data-lint stays **off** (repo DB is SQLite,
  blocked on the upstream `data_lint` SQLite backend — `knowledge/questions/data-lint-sqlite-backend.md`).
- **psc-monitor** — at beacon `c8d344a`, commits `274c0e4` + `7d0875d` (local, unpushed) from its
  2026-07-15 sync. Scaffold HEAD `6ba66dc`'s only later commit added a non-scaffold `plans/` doc, so
  psc-monitor is scaffold-content-current. Per-repo caveats: `[boot_surface_lint]` override 100K/120K;
  ratchet-log seeded; 4 Postgres `data-lint` invariants live; osv-scanner (no root lockfile) + deptry
  (no pip dev-extra) idle by choice.

Neither downstream is pushed — push is operator-gated.

## Prior full propagation — 2026-07-04 (historical)
Both downstreams were previously converged 2026-07-04 (extrends beacon `a879317`; psc-monitor commit
`0485daa` / beacon `511843b`); audit layer wired. Superseded by the 2026-07-15 frontier above.

## Shipped locally since 2026-07-15 — NOT yet propagated
None — both downstreams are current. New scaffold-managed changes land here as they ship, awaiting the
next operator-authorized propagation.

## Scanner provisioning gaps (parked)
Surfaced while extrends/psc enabled scanners; see `knowledge/questions/scanner-provisioning-gaps.md`:
`install-tools.sh` gitleaks `go install` embeds no version (fails the `checks.py` version pin);
`$(go env GOPATH)/bin` is not on the non-interactive PATH. Deterministic-audit runbook:
`knowledge/reference/audit-runbook.md`.
