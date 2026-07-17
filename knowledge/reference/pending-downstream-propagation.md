# Pending downstream propagation (operator-gated)

Scaffold-managed changes propagate to downstream repos (`extrends`, `psc-monitor`) via
`scripts/sync_scaffold.py` — an **operator-gated** step, typically run as a batch. This ledger
records scaffold changes that shipped **locally** (to scaffold `main`, unpushed) but are **not yet
propagated**, plus any per-change caveat that matters at propagation time. It is per-repo state (not
scaffold-managed): each repo's propagation frontier differs, so this file does not itself propagate.

## NOT yet propagated — `reconcile-parked-backlog` (shipped 2026-07-17, beacon `80e7a06`)

Both downstreams are now **behind** — confirmed by a read-only `sync_scaffold.py --check`. This change
touched 15 scaffold-managed files: `scripts/{freeze_check,knowledge_lint,test_freeze_check,test_knowledge_lint}.py`,
`.claude/agents/archive-executor.md` + `.opencode/agents/archive-executor.md` (byte-identical pair —
guarded by `test_executor_body_agreement.py`), `.claude/skills/openspec-archive-change/SKILL.md`,
`knowledge/README.md`, and the frontmatter of 6 audit/workflow skills.

Caveats that matter at propagation time:
- **`knowledge_lint`'s `plans/` gather is now recursive** (excluding `plans/archive/`). This is a
  *widening*, not a relaxation: a downstream repo with nested live plans under `plans/<sub>/` will see
  **new** `closed-but-unpruned` findings that never fired before, and its live-tree doc-lint gate will
  go red on them. Expect to triage real findings per repo — do not assume a clean sync.
- **`scaffold_lint`'s scan vocabulary is now tombstone-derived.** A downstream repo whose docs still
  reference a retired skill name (`lint-knowledge`, `outstanding-work-review`, `openspec-onboard`)
  will now get a `dangling-skill-refs` finding that was previously invisible. That is the point of the
  change, but it means the first sync may surface latent references. The scaffold's own scanned surface
  was verified clean before shipping; the downstreams were not checked.
- `freeze_check` bold-tolerance and the archive follow-on obligation are pure widenings/instructions —
  no downstream findings expected.
- `knowledge/README.md` gained the author-facing `<!-- lint:planned -->` marker documentation.

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
_(none — both downstreams converged to scaffold HEAD `432345e` on 2026-07-16; see frontier above.)_

## Scanner provisioning gaps (parked)
Surfaced while extrends/psc enabled scanners; see `knowledge/questions/scanner-provisioning-gaps.md`:
`install-tools.sh` gitleaks `go install` embeds no version (fails the `checks.py` version pin);
`$(go env GOPATH)/bin` is not on the non-interactive PATH. Deterministic-audit runbook:
`knowledge/reference/audit-runbook.md`.
