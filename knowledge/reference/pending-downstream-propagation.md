# Pending downstream propagation (operator-gated)

Scaffold-managed changes propagate to downstream repos (`extrends`, `psc-monitor`) via
`scripts/sync_scaffold.py` — an **operator-gated** step, typically run as a batch. This ledger
records scaffold changes that shipped **locally** (to scaffold `main`, unpushed) but are **not yet
propagated**, plus any per-change caveat that matters at propagation time. It is per-repo state (not
scaffold-managed): each repo's propagation frontier differs, so this file does not itself propagate.

## Frontier — both downstreams current as of 2026-07-18 (beacon `36adc01`)

Both downstreams converged to scaffold HEAD `36adc01` in the 2026-07-18 sync, which carried the five
items formerly listed as NOT-yet-propagated: **`roll-decisions-index`**, **`graduate-sast-scanners`**,
**`git-native-commit-gate`**, **`custom-checks-family-fix`**, and **`detect-truncated-stream`**.

Pre-sync audit: the deletion pass was a **no-op** in both repos (no `STALE` targets — the retired
`openspec-onboard`, `lint-knowledge`, `outstanding-work-review`, and `audit_bundle.py` entries were
already absent). `--check-refs` was clean pre-sync in both; the only clobber candidate
(`knowledge/README.md`) held a single stale decisions-registry description line, correctly replaced
by the sync.

How the predicted caveats actually landed:
- **decisions-registry pre-roll** — **psc-monitor** needed none (its INDEX was already 12,884 B, under
  the 16,000-byte default, from its earlier hand-condense). **extrends** needed it: INDEX was
  **64,898 B** (4x over budget). Ran `roll_decisions.py` — rolled **105 of 113 entries** verbatim into
  a new `knowledge/decisions/HISTORY.md`, retaining the 8 newest (INDEX now 10,724 B) with a
  load-on-demand pointer line; byte-conserving (no entry dropped). This cleared the new
  `knowledge_lint` budget check AND the `README -> HISTORY.md` dangling ref the sync introduced.
- **git-native commit gate wiring** — wired in **both** via `core.hooksPath=scripts/githooks`.
  psc-monitor: `setup-hooks.sh` set it cleanly (was unset). extrends: `core.hooksPath` was pinned to a
  vestigial explicit `.git/hooks` (samples only, no real hook — confirmed by the wave-4
  correctness-audit finding), so `setup-hooks.sh` conflict-aborted by design; it was set manually per
  the script's own guidance and proven functional (`git rev-parse` resolves to the tracked hook; a dry
  run passed the full gate).
- **SAST scanners / custom-checks `family=` / truncated-stream** — all propagate byte-identical via the
  manifest; all additive and backward-compatible, so none reddened a downstream gate. Neither scanner
  auto-enables (default-disabled). `knowledge/reference/security-scanners.md` is per-repo knowledge and
  was NOT added downstream in this sweep (deferred; scanners stay off, so no gate impact).

Per-repo reconciliation done at this sync (info-preserving — nothing deleted, nothing buried):
- **psc-monitor** — beacon `36adc01`, commit `4281dcb` (local, unpushed). No knowledge reconciliation
  needed: all six gates green on sync (full suite, ruff, `knowledge_lint`, `boot_surface` 77,943 B
  **OK** — no longer WARN; it dropped under its 100K warn threshold since the 2026-07-17 note). Hook
  wired. Standing per-repo caveats (unchanged): `[boot_surface_lint]` override 100K/120K; ratchet-log
  seeded; 4 Postgres data-lint invariants live; osv-scanner + deptry idle by choice; pyproject `dev`
  extra declares `ruff==0.15.16` in `.venv`.
- **extrends** — beacon `36adc01`, sync commit `65c2459` + fix commit `15b9fc6` (local, unpushed).
  Pre-roll done (above). **Three PRE-EXISTING gate failures** (from commit `c6b3caf` + STATUS.md
  history, NOT sync-caused — they only surfaced when the full gate ran during propagation) were fixed
  in `15b9fc6` so the git-native hook could be wired without blocking commits: ruff I001 + format drift
  in two `scripts/_*_oneoff.py` probe scripts (auto-fixed), and a `knowledge/STATUS.md` latest-change
  entry 8 words over the 150-word `status_lint` cap (trimmed filler, all facts preserved). Full gate
  now green (2396 passed); boot surface **80,728 B** — under even the default budget after the roll, so
  the `[boot_surface_lint]` 120K/140K override now carries large headroom. Standing per-repo caveats
  (unchanged): handoff-named files `*-notes.md`; `knowledge/ratchet-log.md` seeded (zero entries);
  data-lint stays off (SQLite; `checks.toml` not re-wired to the SQLite backend); pyproject `dev` extra
  declares `ruff==0.15.16` in `.venv`.
  **Flag (not actioned):** the 2026-07-17 note said do-not-prune the `gold-pilot3-resume-*.md` plans
  "until pilot-3 archives." Pilot-3 has since concluded **NOT ADOPTED** and `gold-anchor-v1-2` is
  archived in extrends (change `gold-anchor-v1-2`), so those resume runbooks and the
  `knowledge/HANDOFF.md` that boot-points at them may now be prunable — left for operator triage, not
  pruned here.

Gates verified green by hand in both repos before commit (sync commits use `--no-verify`, the
sanctioned escape for a deliberate sync): full suite, `ruff check`, `ruff format --check`,
`status_lint`, `knowledge_lint`, `boot_surface_lint`, and `sync_scaffold --check` / `--check-refs`.

Neither downstream is pushed — push is operator-gated.

## Frontier — both downstreams current as of 2026-07-17 (beacon `27adff6`, superseded by the entry above)

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

None — all five items (`roll-decisions-index`, `graduate-sast-scanners`, `git-native-commit-gate`,
`custom-checks-family-fix`, `detect-truncated-stream`) were propagated in the 2026-07-18 frontier
above. Their full records live in `openspec/changes/archive/`.

## Scanner provisioning gaps (parked)
Surfaced while extrends/psc enabled scanners; see `knowledge/questions/scanner-provisioning-gaps.md`:
`install-tools.sh` gitleaks `go install` embeds no version (fails the `checks.py` version pin);
`$(go env GOPATH)/bin` is not on the non-interactive PATH. Deterministic-audit runbook:
`knowledge/reference/audit-runbook.md`.
