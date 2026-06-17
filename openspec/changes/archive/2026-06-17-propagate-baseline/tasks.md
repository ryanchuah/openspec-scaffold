# W6 — propagate-baseline · tasks (runbook)

**Tier:** MEDIUM, runbook-style (lightweight per operator 2026-06-17). W6 edits **no
scaffold-managed file** — it runs `scripts/sync_scaffold.py` against each downstream
repo and wires two per-repo files. The gate is the deterministic post-sync
`--check` convergence (all IDENTICAL) + diff inspection, **not** a separate-model
design review. The snapshot source is scaffold HEAD after W0–W5 archived.

**Order:** extrends first (clean tree), psc-monitor later (it has uncommitted billing
work + an in-flight `invoice-payment-failed-alert` change — sync when its tree settles).

**Per-repo wiring (NOT scaffold-managed, hand-authored per repo):**
- `.claude/settings.json` — PreToolUse hooks: `test-gate.sh` (commit-test gate) +
  `scaffold_check.py` (scaffold-managed guard, downstream-only). extrends had none →
  create; psc-monitor has one with permissions → **merge** a hooks block, don't clobber.
- `scripts/test-cmd` — per-repo commit-gate command. **Dormant by default** (absent =
  no-op), matching scaffold which ships the gate machinery without a test-cmd.

## extrends — DONE 2026-06-17 (commit 176d554, LOCAL/unpushed)
- [x] Option Y relocation: pytrends/TrendScope war-stories → `ai-docs/workflow-lessons.md`
- [x] `sync_scaffold.py /home/pang/Projects/extrends` (exit 0)
- [x] post-sync `--check` = all IDENTICAL (convergence proof)
- [x] diff-review: only managed files changed; AGENTS.md span-merge preserved
      title/`## Project context`/tail; TrendScope content intact
- [x] `.claude/settings.json` created (test-gate + scaffold_check hooks)
- [x] test-cmd: dormant (none created — operator chose match-scaffold)
- [x] synced unit tests: 30 passed (test_convergence + test_executor_body_agreement)
- [x] `openspec validate --strict`: 15 specs clean
- [x] live guard smoke: scaffold_check.py exits 2 on a staged managed file (closes W1 follow-up)
- [x] scoped commit (`git add -- <explicit paths>`, `git commit --no-verify`)

## psc-monitor — PENDING (separate session, when tree is clean)
- [ ] (no relocation needed — pure lag, no unique content)
- [ ] `sync_scaffold.py /home/pang/Projects/psc-monitor`
- [ ] post-sync `--check` = all IDENTICAL
- [ ] diff-review: only managed files changed (billing.py / STATUS.md / in-flight
      change must stay untouched — stage by explicit path, never `-A`)
- [ ] `.claude/settings.json` — **merge** hooks block into existing (preserve permissions)
- [ ] test-cmd: dormant unless its Postgres-backed suite is gate-safe
- [ ] synced unit tests + `openspec validate --strict`
- [ ] live guard smoke (exit 2)
- [ ] scoped commit (`--no-verify`)

## Close-out (after psc-monitor lands)
- [ ] delete superseded `openspec/changes/scaffold-sync/` (untracked, frozen)
- [ ] commit the design records (`ai-docs/consolidation-plan-2026-06-16.md`,
      `ai-docs/workflow-audit-2026-06-16.md`)
- [ ] reconcile STATUS.md + decisions.md + improvement-roadmap.md; archive this change
