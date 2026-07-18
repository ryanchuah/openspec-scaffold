# Pending downstream propagation (operator-gated)

Scaffold-managed changes propagate to downstream repos (`extrends`, `psc-monitor`) via
`scripts/sync_scaffold.py` — an **operator-gated** step, typically run as a batch. This ledger
records scaffold changes that shipped **locally** (to scaffold `main`, unpushed) but are **not yet
propagated**, plus any per-change caveat that matters at propagation time. It is per-repo state (not
scaffold-managed): each repo's propagation frontier differs, so this file does not itself propagate.

## Frontier — both downstreams current as of 2026-07-17 (beacon `27adff6`)

Both downstreams converged to scaffold HEAD `27adff6` in the 2026-07-17 sync, which carried the two
items formerly listed as NOT-yet-propagated: **`reconcile-parked-backlog`** (recursive `plans/`
gather, `freeze_check` bold-tolerance, archive follow-on obligation, archive-executor pair) and
**`handoff-lint-exempt`** (`knowledge/HANDOFF.md` exempted as a scanned source in `knowledge_lint.py`
and `sync_scaffold.py --check-refs`).

Pre-sync audit: every changed scaffold-managed file was verified **byte-identical to the `a2a450c`
baseline** in both repos before syncing — i.e. zero local downstream edits, so nothing was clobbered.
The deletion pass was a **no-op** in both repos (no `STALE` targets; the retired `openspec-onboard`,
`lint-knowledge`, `outstanding-work-review` and `audit_bundle.py` entries were already absent).

How the predicted caveats actually landed:
- **Recursive `plans/` gather** — fired in **psc-monitor only** (one nested plan reached for the first
  time; see below). **extrends** gained **no** new findings: its nested plan dirs were already clean.
- **`scaffold_lint` tombstone-derived vocabulary** — **no downstream surface**: `scaffold_lint.py` is
  scaffold-only and is not in `scaffold_manifest.txt`, so it does not propagate. The predicted
  `dangling-skill-refs` exposure did not apply.
- **`duplicate_scan_dirs` re-widening** — **moot**: neither downstream configures `duplicate_scan_dirs`
  in its `checks.toml`. (The related still-open leak of the same class affecting the pre-existing
  `knowledge/research/` exclusion remains tracked at
  `knowledge/questions/research-exclusion-scan-dir-leak.md`.)
- **handoff exemption** — latent-but-relevant in **extrends**, which currently carries a live
  `knowledge/HANDOFF.md`. That file was not tripping the checks at sync time, so the exemption
  removed no existing finding; it protects future handoffs there.

Per-repo reconciliation done at this sync (info-preserving — nothing deleted, nothing buried):
- **psc-monitor** — beacon `27adff6`, commit `4968909` (local, unpushed).
  `psc-monitor/plans/pro-tier-repricing/plan.md` retained with `<!-- lint:keep -->` + rationale. The
  recursive gather reached this nested plan for the first time and flagged its `DONE` task markers.
  **Not prunable:** it is a SMALL-tier change, which skips the archive lifecycle, so that repo's
  `plans/` tree *is* the durable record — and its `psc-monitor/knowledge/STATUS.md` cites
  `psc-monitor/plans/pro-tier-repricing/` as exactly that record, with open follow-ons in
  `psc-monitor/knowledge/questions/sp05-pricing-follow-ons.md`.
  (Downstream paths in this file are repo-prefixed deliberately: they are cross-repo citations, and
  an unprefixed `plans/` path would be ambiguous with this repo's own tree.)
  Standing per-repo caveats (unchanged): `[boot_surface_lint]` override 100K/120K in `checks.toml`;
  ratchet-log seeded; 4 Postgres `data-lint` invariants live; osv-scanner (no root lockfile) + deptry
  (no pip dev-extra) idle by choice; pyproject `dev` extra declares `ruff==0.15.16` in `.venv`.
  **Watch:** boot surface is WARN and sits close to its 120K FAIL threshold — a small growth in the
  boot files will turn the commit gate red. Worth a condense-vs-raise call before it trips.
- **extrends** — beacon `27adff6`, commit `ba085ae` (local, unpushed).
  `extrends/plans/gold-pilot3-resume-2026-07-16.md` and its `-2026-07-17.md` sibling retained with
  `<!-- lint:keep -->` + rationale. Both tripped `closed-but-unpruned` on their
  `## STATE — what is DONE (do NOT redo)` headings — **false positives**. Both are live resume
  runbooks for the in-flight, un-archived COMPLEX change `gold-anchor-v1-2` (pilot-3 paused on a
  Gemini **daily-quota** block, resuming ~2026-07-18); that repo's `extrends/knowledge/HANDOFF.md`
  boot-points at them, and the flagged heading is what stops a resuming agent from re-running the
  ~250 paid pro-tier calls that exhausted the quota. **Do not prune until pilot-3 archives.**
  Both findings **pre-dated** this sync — extrends' live-tree doc-lint gate was already red before it,
  and is now green for the first time since those plans landed.
  Standing per-repo caveats (unchanged): `[boot_surface_lint]` override 120K/140K; handoff-named files
  renamed `*-handoff.md` → `*-notes.md`; `knowledge/ratchet-log.md` seeded (zero entries); data-lint
  stays **off** (repo DB is SQLite; the upstream `data_lint.py` SQLite backend has shipped, but
  extrends' `checks.toml` has not been re-wired to use it); pyproject `dev` extra declares
  `ruff==0.15.16` in `.venv`.

Gates verified green by hand in both repos before commit (the sync commit uses `--no-verify`, the
sanctioned escape for a deliberate sync, which also skips the test gate): full suite, `ruff check`,
`ruff format --check`, `knowledge_lint`, and `sync_scaffold --check` / `--check-refs`.
`boot_surface_lint` is WARN (exit 1) in both — acceptable; neither FAILs.

Neither downstream is pushed — push is operator-gated.

## Frontier — both downstreams current as of 2026-07-16 (superseded by the entry above)
Both converged to scaffold HEAD (beacon `a2a450c`) in the 2026-07-16 sync. It carried the two items
formerly in "NOT yet propagated" — `split-outstanding-work-skills` (outstanding-work-review →
outstanding-work-scan + new outstanding-work-deep-sweep; old dir removed via tombstone) and the
`7f23eda` knowledge_lint gitignored-citation exemption — plus the `a2a450c` `test_check_sh`
multi-ruff PATH fix (`_env_without_ruff` now scrubs every ruff dir from PATH, not just the first —
needed once a repo carries ruff in its own venv alongside a system ruff). No per-repo knowledge
reconciliation was needed (the knowledge_lint change is a relaxation — no new checks fired;
`--check`/`--check-refs` clean; full suites + ruff green on both before commit).
- **extrends** — beacon `a2a450c`, commits `f671791` + `416a163` + `8271c3b` (local, unpushed).
  Standing per-repo caveats (unchanged): `[boot_surface_lint]` override 120K/140K in `checks.toml`;
  handoff-named files renamed `*-handoff.md` → `*-notes.md`; `knowledge/ratchet-log.md` seeded (zero
  entries). Data-lint stays **off** (repo DB is SQLite; the upstream `data_lint.py` SQLite backend
  has shipped, but extrends' `checks.toml` has not been re-wired to use it). **New 2026-07-16:** pyproject `dev`
  extra now declares `ruff==0.15.16`, installed into `.venv` (same self-contained-lint fix as
  psc-monitor). Full gate verified green with the venv activated.
- **psc-monitor** — beacon `a2a450c`, commits `c83fed5` + `677240d` (local, unpushed). Standing
  per-repo caveats (unchanged): `[boot_surface_lint]` override 100K/120K; ratchet-log seeded; 4
  Postgres `data-lint` invariants live; osv-scanner (no root lockfile) + deptry (no pip dev-extra)
  idle by choice. **New 2026-07-16:** pyproject `dev` extra now declares `ruff==0.15.16`, installed
  into `.venv` — the lint gate no longer silently depends on a machine-global ruff (`check.sh`
  degrades to WARNING+skip when ruff is unresolvable, so an undeclared ruff meant lint could stop
  running unnoticed). Full gate verified green with the venv activated.

Neither downstream is pushed — push is operator-gated.

## Prior propagations (historical)
- **2026-07-15** — extrends beacon `6ba66dc` / commit `1853b78`; psc-monitor beacon `c8d344a` /
  commits `274c0e4` + `7d0875d`. Carried the 2026-07-04 → 2026-07-15 backlog (wave-1/2 hardening,
  audit skills, archive-mechanization, repo-lint, boot-surface, freeze-check, opencode-delegate,
  delegation-harness single-sourcing, finding-closure-ratchet). Superseded by the 2026-07-16 frontier.
- **2026-07-04** — extrends beacon `a879317`; psc-monitor commit `0485daa` / beacon `511843b`; audit
  layer wired. Superseded above.

## Shipped locally — NOT yet propagated

### `roll-decisions-index` (shipped 2026-07-17)
Adds two manifest files (`scripts/roll_decisions.py`, `scripts/test_roll_decisions.py`) and modifies
`scripts/knowledge_lint.py`, `scripts/boot_surface_lint.py`, and `knowledge/README.md`.

Caveat that matters at propagation time:
- **Requires a per-repo roll before the new gate lands.** Each downstream repo must run
  `python3 scripts/roll_decisions.py` against its own tree during its propagation session, BEFORE its
  live-tree `knowledge_lint` gate sees the new `decisions-index-budget` check. Status as of
  2026-07-18: **psc-monitor already condensed** (its own `boot-surface-condense` commit `affce4e`
  rolled its registry to `knowledge/decisions/HISTORY.md` by hand — its INDEX is now under the
  16,000-byte default, so no pre-roll is needed there); **extrends has NOT** — its
  `knowledge/decisions/INDEX.md` is still well over budget and would redden its gate on sync
  without the pre-roll.

### `graduate-sast-scanners` (shipped 2026-07-18)
Adds Semgrep + Bandit as built-in parsed checks in `checks.py` (heavy-tier, default-disabled,
version-recorded-not-gated), restructures `install-tools.sh` so Go-absence no longer short-circuits
pip provisioning, documents both in `knowledge/reference/security-scanners.md`, and extends
`test_checks.py`.

Caveats that matter at propagation time:
- **Scaffold-managed files propagate byte-identical:** `scripts/checks.py`, `scripts/install-tools.sh`,
  `scripts/test_checks.py`, and `scripts/check.sh` sync via the manifest — no manual step.
- **`knowledge/reference/security-scanners.md` is per-repo knowledge (NOT manifest):** each
  downstream repo needs the semgrep/bandit documentation added by hand during the propagation sweep.
- **Neither scanner auto-enables:** both are default-disabled, so the sync won't red any downstream
  gate. Each repo opts in via `[checks.<name>] enabled = true`. Semgrep additionally requires a
  `--config <ruleset>` supplied via `[checks.semgrep] args`; without it, an enabled semgrep
  INFRA-FAILs.

### `git-native-commit-gate` (shipped 2026-07-18)
Adds a git-native `pre-commit` hook (`scripts/githooks/pre-commit`) as the primary,
spelling-agnostic, cross-agent commit-test-gate enforcement layer, wired via
`git config --local core.hooksPath scripts/githooks` (new `scripts/setup-hooks.sh`); the Claude
`PreToolUse` `scripts/test-gate.sh` now defers to it (fail-safe) instead of always running
`check.sh`. New scaffold-managed files: `scripts/githooks/pre-commit`, `scripts/setup-hooks.sh`,
`scripts/test_githook_pre_commit.py`, `scripts/test_gate_defer.py` (+ manifest entries). Modified
scaffold-managed files: `scripts/test-gate.sh` (fail-safe defer branch), `AGENTS.md` (cross-agent
carve-out).

Caveats that matter at propagation time:
- **Scaffold-managed files propagate byte-identical, including the exec bit:** `sync_scaffold.py`
  uses `shutil.copy2`, which preserves the executable bit on `scripts/githooks/pre-commit` and
  `scripts/setup-hooks.sh` — verified during this change, no manual step needed for the files
  themselves.
- **Per-repo manual sweep required:** each downstream clone must run `bash scripts/setup-hooks.sh`
  once to wire `core.hooksPath` — this is `.git/config` state, not tracked/cloned, so sync alone does
  not activate the hook.
- **`knowledge/reference/new-repo-bootstrap.md` is scaffold-local (NOT synced):** its new
  `setup-hooks.sh` bootstrap step must be added to each downstream's own bootstrap doc by hand.
- **Downstream `.claude/settings.json` keeps its `PreToolUse` test-gate entry** — it is now the
  fail-safe fallback (not removed), so no downstream settings edit is required by this change.

## Scanner provisioning gaps (parked)
Surfaced while extrends/psc enabled scanners; see `knowledge/questions/scanner-provisioning-gaps.md`:
`install-tools.sh` gitleaks `go install` embeds no version (fails the `checks.py` version pin);
`$(go env GOPATH)/bin` is not on the non-interactive PATH. Deterministic-audit runbook:
`knowledge/reference/audit-runbook.md`.
