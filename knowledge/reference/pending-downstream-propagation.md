# Pending downstream propagation (operator-gated)

Scaffold-managed changes propagate to downstream repos (`extrends`, `psc-monitor`) via
`scripts/sync_scaffold.py` — an **operator-gated** step, typically run as a batch. This ledger
records scaffold changes that shipped **locally** (to scaffold `main`, unpushed) but are **not yet
propagated**, plus any per-change caveat that matters at propagation time. It is per-repo state (not
scaffold-managed): each repo's propagation frontier differs, so this file does not itself propagate.

## Frontier — both downstreams current as of 2026-07-16
Both converged to scaffold HEAD (beacon `432345e`) in the 2026-07-16 sync, which carried the two
items formerly in "NOT yet propagated": `split-outstanding-work-skills` (outstanding-work-review →
outstanding-work-scan + new outstanding-work-deep-sweep; old dir removed via tombstone) and the
`7f23eda` knowledge_lint gitignored-citation exemption. No per-repo knowledge reconciliation was
needed (the knowledge_lint change is a relaxation — no new checks fired; `--check`/`--check-refs`
clean; full suites + ruff green on both before commit).
- **extrends** — beacon `432345e`, commit `f671791` (local, unpushed). Standing per-repo caveats
  (unchanged by this sync): `[boot_surface_lint]` override 120K/140K in `checks.toml`; handoff-named
  files renamed `*-handoff.md` → `*-notes.md`; `knowledge/ratchet-log.md` seeded (zero entries).
  Data-lint stays **off** (repo DB is SQLite, blocked on the upstream `data_lint` SQLite backend —
  `knowledge/questions/data-lint-sqlite-backend.md`).
- **psc-monitor** — beacon `432345e`, commit `c83fed5` (local, unpushed). Standing per-repo caveats
  (unchanged by this sync): `[boot_surface_lint]` override 100K/120K; ratchet-log seeded; 4 Postgres
  `data-lint` invariants live; osv-scanner (no root lockfile) + deptry (no pip dev-extra) idle by
  choice. Note: psc-monitor's gate resolves `ruff` from the system PATH (`~/.local/bin/ruff`), not a
  venv-local binary.

Neither downstream is pushed — push is operator-gated.

## Prior propagations (historical)
- **2026-07-15** — extrends beacon `6ba66dc` / commit `1853b78`; psc-monitor beacon `c8d344a` /
  commits `274c0e4` + `7d0875d`. Carried the 2026-07-04 → 2026-07-15 backlog (wave-1/2 hardening,
  audit skills, archive-mechanization, repo-lint, boot-surface, freeze-check, opencode-delegate,
  delegation-harness single-sourcing, finding-closure-ratchet). Superseded by the 2026-07-16 frontier.
- **2026-07-04** — extrends beacon `a879317`; psc-monitor commit `0485daa` / beacon `511843b`; audit
  layer wired. Superseded above.

## Shipped locally — NOT yet propagated
_(none — both downstreams converged to scaffold HEAD `432345e` on 2026-07-16; see frontier above.)_

## Scanner provisioning gaps (parked)
Surfaced while extrends/psc enabled scanners; see `knowledge/questions/scanner-provisioning-gaps.md`:
`install-tools.sh` gitleaks `go install` embeds no version (fails the `checks.py` version pin);
`$(go env GOPATH)/bin` is not on the non-interactive PATH. Deterministic-audit runbook:
`knowledge/reference/audit-runbook.md`.
