# Explore brief — day-to-day tooling layer (portfolio)

**Date:** 2026-07-03 · **Origin:** operator + departing-principal review session (scaffold repo).
Supersedes and absorbs `knowledge/HANDOFF.md` (audit-tooling clarity gap), which is deleted on
this brief's creation.

## Problem

The scaffold ships a deterministic audit layer (`audit_bundle.py` + `audit_scope.py` + the
`run-audit` skill), but day-to-day development in the downstream repos (`extrends`,
`psc-monitor`) has **no continuous quality layer at all**:

1. **Lint exists only inside audits.** Neither downstream repo has a ruff config; ruff is not
   even a declared dev dependency. The unconfigured default ruleset already reports a
   substantial backlog in extrends (majority auto-fixable) and `ruff format` has never been
   enforced. The audit keeps re-detecting the same backlog — wasted triage every cycle,
   zero prevention between cycles.
2. **The only commit gate is Claude-private.** The commit-test-gate is a `PreToolUse` hook in
   `.claude/settings.json`; OpenCode/DeepSeek executors and humans commit ungated. CI in both
   repos runs tests only — no lint, no format check, no secret/vulnerability scanning.
3. **"Audit" branding causes category confusion.** A downstream agent running the standard
   `run-audit` cycle escalated *confused* (missing gitleaks/deptry binaries → opaque
   INFRA-FAIL; stop-on-first-failure hid the other missing tools and prevented the
   inventory snapshot from running; first-run `audit-log.md` absence unexplained). Also, the
   bundle's *fact-generating* outputs (inventory snapshot: file tree, entry points, env vars;
   hotspot ranking) are useful to ANY agent orienting day-to-day, but are locked behind
   audit-branded, operator-invoked tooling.
4. **Renames/removals don't propagate.** `sync_scaffold.py` copies manifest files but has no
   deletion mechanism — the `openspec-onboard` removal needed a hand-deleted tombstone, and
   any rename repeats that manual sweep per repo.
5. **Doc-lints rely on memory.** `knowledge_lint.py` / `status_lint.py` run only when a
   skill/agent remembers; only `scaffold_lint.py` is self-enforcing (lives in the pytest
   suite → commit gate). Conventions without mechanisms decay: extrends carries tracked
   root `HANDOFF-*` files that contradict the shipped knowledge-handoff-file decision.

## Root cause

The tooling was designed audit-first: detection concentrated in an occasional ceremony
instead of layered by consumption pattern. There are three distinct patterns with three
correct triggers, currently collapsed into one:

- **Gates** (binary pass/fail: lint, format, tests, doc-structure) → must fire on events
  (commit, push), zero memory.
- **Facts** (can't fail; describe the repo: inventory, hotspots) → regenerate at point of
  use; cache semantics.
- **Audit** (judgment-tier leads: dead code, duplication, complexity, index leads; semantic
  drift; architecture review) → periodic operator-invoked ceremony; record semantics
  (tag + log).

## Direction

**Principle: policy lives upstream and auto-propagates; downstream keeps only one-time
invocation glue.** No ongoing manual per-repo sweeps.

Portfolio of five changes, sequential:

### B — sync deletion manifest (scaffold, SMALL)
`sync_scaffold.py` gains a removed-paths list (e.g. `scaffold_manifest_removed.txt`);
sync deletes those paths downstream. Tests. Unblocks clean renames (A) and retires the
hand-tombstone procedure (also covers the stale `openspec-onboard` dir still in psc-monitor).

### A — checks/facts split + informed failures (scaffold, MEDIUM)
Rework `audit_bundle.py` into two entry points over the one engine/registry/contract:
- **checks** (detectors: ruff, gitleaks, osv-scanner, deptry, jscpd, vulture, data-lint) →
  dated reports `output/checks/<date>/`, findings-vs-clean exit codes.
- **facts** (inventory, scope/hotspots, complexity metrics, index leads) → undated
  regenerate-on-use `output/facts/`, always exit 0. Inventory gains a "last audit anchor +
  commits since" staleness field.
- Config `audit.toml` → `checks.toml` (no repo has one yet — zero migration).
- **Preflight**: report ALL enabled-but-missing tools at once instead of
  stop-on-first-failure serial discovery; keep stop-on-first-failure for genuine mid-run
  infra failures; keep the hard-fail forcing function (an enabled security tool that is
  absent must fail, never silently skip).
- **Self-explaining failures**: INFRA-FAIL messages carry resolution guidance
  (install X, or disable via `[checks.X] enabled = false` — noting what coverage is lost);
  `--list` summarizes enabled-but-unavailable; first-run hint when `audit-log.md` absent.
- `audit_scope.py`, `audit/<date>` tags, `knowledge/audit-log.md`, and the `run-audit`
  skill keep the audit name (the ceremony is genuinely an audit). Skill updated: new names,
  what runs when, enabled-vs-installed distinction, staleness-triggered cadence, and an
  annual "re-justify the suppression baseline/whitelist" reminder.
- Old filenames go on the removed-paths list (B).

### C — shared lint layer / one definition of green (scaffold, MEDIUM)
- Scaffold-managed **`ruff.toml`** (modest curated ruleset + format; repo-specific
  per-file-ignores live in the shared file — unmatched paths are harmless).
- Scaffold-managed **`scripts/check.sh`**: ruff check + `ruff format --check` + delegate to
  per-repo `scripts/test-cmd`. `test-gate.sh` calls `check.sh` → Claude hook picks it up by
  sync; CI and humans call the same script. One canonical "green".
- Scaffold-managed **`scripts/install-tools.sh`** (pinned gitleaks/osv-scanner installs;
  deptry via dev extras).
- Scaffold-managed live-tree test wiring `knowledge_lint.py` + `status_lint.py` into the
  pytest suite (mirrors `scaffold_lint.py`), converting doc-lints from memory to gate.
- New deterministic check: no root `HANDOFF*`/`HANDOVER*` files (mechanizes the
  knowledge-handoff-file decision).
- Apply skill gains the autofix habit: `ruff check --fix` + format on touched files before
  reporting done.
- Scaffold's own lint baseline fixed in the same change (gate must land green).

### D1 — extrends wiring (downstream, SMALL, after operator-gated sync)
One-time glue: CI step `run: scripts/check.sh`; `just check` / `just tools` targets;
dev-extras pins (ruff, deptry); run install-tools; one-time `ruff --fix` + format baseline
commit; seed `checks.toml`; knowledge-lint burn-down (owed already); align CI Python with the
actual dev interpreter; root hygiene sweep (tracked HANDOFF files → knowledge conventions or
deletion — operator sign-off; `tmp/`/`test-smoke/` ignored or removed).

### D2 — psc-monitor unfreeze + wiring (downstream, SMALL, after operator-gated sync)
The frozen pending batch PLUS A/B/C in one sync (deletion manifest handles tombstones).
Then same wiring as D1 (Makefile targets), plus minimal frontend lint (ESLint + `tsc
--noEmit` + CI step) per the parked deterministic-tooling wiring plan; `plans/` cleanup.

## Out of scope (parked explicitly)
- Type-checking (pyright) — measure first, decide per repo later.
- Dependabot/renovate — operator decision; noted that pinned deps currently have no update
  mechanism and CVE drift is only caught at audit time.
- DB-snapshot retention convention in extrends.
- Any change to lifecycle skills beyond the apply-autofix line and run-audit updates.

## Operator gates preserved
Downstream sync and pushes stay operator-authorized per AGENTS.md; `audit_scope.py tag`
stays the sole repo-state mutation, operator-gated; hygiene deletions in D1/D2 are
presented before deletion.

## Post-review clarifications (direction gate 2026-07-03, PREMISE: AGREE)

- **`checks.toml` is per-repo one-time glue, not scaffold-managed** — it encodes per-repo
  realities (which external tools are installed, enable/disable decisions, repo paths).
  Change A ships a documented seed convention; D1/D2 create each repo's file once.
- **The incident fix is A's preflight + self-explaining failures; the checks/facts/audit
  rename is structural hygiene.** Implementers should weight effort accordingly.
- **Doc-lint gap verified precisely:** `knowledge_lint.py`/`status_lint.py` are already
  scaffold-managed and shipped downstream, but their tests are fixture-only — nothing runs
  them against the live tree at commit time. C adds the live-tree gate, nothing more.
- **Dependency chain, explicit:** B → A (renames need the deletion manifest) → C →
  operator-gated sync → D1 (extrends) and, after unfreeze authorization, D2 (psc-monitor).
  A and C are independent of each other but run sequentially (single working tree).
- **Security-scanner CI starting default:** blocking on push to `main`; per-PR left to C's
  design to settle (runtime/false-positive cost).
- This brief is **portfolio-level**; each change gets its own `openspec/changes/<name>/`
  artifacts at propose time.

## Operator decisions (2026-07-03, portfolio confirmed — B: SMALL, A: MEDIUM, C: MEDIUM, D1/D2: SMALL)
- `ruff.toml` ruleset: **E, F, I, B + enforced format** (ratchet wider later).
- Security scanners (gitleaks/osv-scanner) in CI: **blocking on pushes AND PRs**
  (operator chose stricter than the reviewer-endorsed main-only default).
- extrends tracked root handoff files: **list per-file with summaries for operator
  approval before any deletion/relocation** (D1).
- extrends CI Python alignment: match CI to the dev interpreter (default accepted).
- Naming is three words (checks/facts/audit) where there was one — mitigated by entry-point
  separation making wrong combinations impossible (facts can't tag; gates don't run facts).
