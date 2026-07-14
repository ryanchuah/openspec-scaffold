# Pending downstream propagation (operator-gated)

Scaffold-managed changes propagate to downstream repos (`extrends`, `psc-monitor`) via
`scripts/sync_scaffold.py` — an **operator-gated** step, typically run as a batch. This ledger
records scaffold changes that shipped **locally** (to scaffold `main`, unpushed) but are **not yet
propagated**, plus any per-change caveat that matters at propagation time. It is per-repo state (not
scaffold-managed): each repo's propagation frontier differs, so this file does not itself propagate.

## Last full propagation — 2026-07-04 (both downstreams, local & unpushed)
- **extrends** — converged to scaffold HEAD (beacon `a879317`); audit layer wired. Data-lint stays
  off (repo DB is SQLite, blocked on the upstream `data_lint` SQLite backend —
  `knowledge/questions/data-lint-sqlite-backend.md`). Operator pruning of the relocated
  handoffs-archive dir + 2 untracked root handoff files still pending.
- **psc-monitor** — propagated (commit `0485daa`, beacon `511843b`); audit layer wired (4 Postgres
  `data-lint` invariants live). osv-scanner (no root lockfile) + deptry (no pip dev-extra) idle by
  choice.

Two scaffold fixes shipped **during** that propagation: the lint-knowledge removed-manifest
tombstone (`9ea6076`) and the ruff `target-version=py311` cross-repo determinism pin (`a879317`).

## Shipped since 2026-07-04 — NOT yet propagated (deferred, operator-gated)
All shipped to scaffold `main` locally (unpushed), awaiting a fresh operator propagation
authorization. Several arrive **INERT** on first sync (auto-disabled until a downstream repo opts
in), so batching them is low-risk:
- **correctness-audit-skill** (2026-07-13) — new skill + marker-gated dossier lint; INERT until a
  repo authors a marked dossier.
- **verify-stack-redirect** (2026-07-13) — manifest-tracked skill/agent/AGENTS.md edits. (Root
  `README.md`, not scaffold-managed, was reconciled directly — no downstream sweep.)
- **lesson-check-ratchet** (2026-07-13) — `repo_lint.py` / `knowledge_lint.py` ratchet checks + two
  skill triage steps; framework arrives INERT (no `checks/*.py`, no per-repo ledger → auto-disabled,
  lint-guarded); per-repo adoption is separate downstream SMALL work.
- **outstanding-and-continuity-hardening** (2026-07-13) — widened handoff-file lint; **coupled** to a
  downstream cleanup: extrends (~27) + psc-monitor handoff-named files must be renamed/archived
  first, else the widened lint reddens both repos' pytest gates. See
  `knowledge/questions/continuity-file-downstream-cleanup.md`.
- **lifecycle-skill-hardening** (2026-07-13) — scaffold-only SMALL lifecycle-skill fixes.
- **Wave-1/2 hardening batch** (2026-07-13/14) — `defect-prevention-detectors` (OW-1+4),
  `instruction-surface-coherence` (OW-9+14), `delegation-wrapper-telemetry` (OW-7),
  `apply-throughput-resume` (OW-10), `skill-debloat-gates` (OW-11 mechanized half), and
  `verify-adversarial-fixtures` — all edit scaffold-managed skills / config / detectors.
- **knowledge-surface-bounding-2** (2026-07-14) — `status_lint.py`, new `boot_surface_lint.py`,
  `scaffold_manifest.txt`. Downstream will **FAIL** `boot_surface_lint` on first sync (extrends is
  ~122KB boot surface today) — the intended signal; cleaning that up is separate downstream work.

## Scanner provisioning gaps (parked)
Surfaced while extrends/psc enabled scanners; see `knowledge/questions/scanner-provisioning-gaps.md`:
`install-tools.sh` gitleaks `go install` embeds no version (fails the `checks.py` version pin);
`$(go env GOPATH)/bin` is not on the non-interactive PATH. Deterministic-audit runbook:
`knowledge/reference/audit-runbook.md`.
