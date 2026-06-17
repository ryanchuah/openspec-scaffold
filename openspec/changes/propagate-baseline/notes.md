# W6 — propagate-baseline · notes

## Tier & process
- **MEDIUM, runbook-style.** Lightweight per operator decision (2026-06-17): W6 runs a
  mechanical sync and wires per-repo files; it edits no scaffold-managed file, so the
  full propose→pro-review→apply→verify→archive lifecycle is over-process. The gate is
  deterministic: post-sync `sync_scaffold.py --check <repo>` must report **all
  IDENTICAL**, plus a diff-review that only managed files changed.
- **LAST in the W-family.** Snapshots scaffold HEAD after W0–W5 archived
  (`ai-docs/consolidation-plan-2026-06-16.md` §2 "propagation is a SNAPSHOT event").
- **Not auto-advancing.** extrends done this session; psc-monitor is phase-gated to a
  later session when its working tree is clean.

## Acceptance criteria (per repo)
1. `sync_scaffold.py <repo>` exits 0; subsequent `--check` reports every manifest entry
   IDENTICAL.
2. `git diff` shows only manifest-managed files + the MISSING-file creations; AGENTS.md
   changed only within the shared workflow span (per-repo title, `## Project context`,
   and tail preserved).
3. The downstream synced unit tests pass (`test_convergence.py`,
   `test_executor_body_agreement.py`) and `openspec validate --strict` is clean.
4. `.claude/settings.json` wires both PreToolUse hooks; the live guard smoke confirms
   `scaffold_check.py` exits 2 on a staged managed file.
5. Commit is scoped by explicit path and uses `--no-verify` (the sanctioned
   deliberate-sync escape — the new guard otherwise blocks scaffold-managed files).

## Key decisions (operator, 2026-06-17)
- **War-stories: relocate, not clobber (Option Y).** extrends' inline pytrends/TrendScope
  content moved to `ai-docs/workflow-lessons.md` before sync. psc-monitor needs none
  (pure lag — its only divergence was the pre-W2 generic harness text).
- **Process: lightweight runbook**, not full openspec lifecycle.
- **Order: extrends first, psc-monitor later** (psc-monitor has uncommitted billing work
  + an in-flight change).
- **test-cmd: dormant** (match scaffold, which ships the gate machinery without a
  test-cmd). Each repo opts in later.

## Provenance
- Mechanism: W1 `fix-sync-mechanism` (`scripts/sync_scaffold.py`, `scaffold_check.py`,
  `scaffold_manifest.txt`); spec `openspec/specs/scaffold-sync-mechanism/spec.md`.
- Map: `ai-docs/consolidation-plan-2026-06-16.md` work-item row **W6** (D7 settings.json,
  D8 test-cmd, D10 drift-check, M2 manual-diff confirm).
- Supersedes the frozen `openspec/changes/scaffold-sync/` (delete at close-out).

## Reconciliation log (to apply at archive, after psc-monitor)
- STATUS.md: W6 partially landed (extrends synced; psc-monitor pending).
- decisions.md: single-source mechanism is now live to extrends; the golden-source→repo
  propagation path is exercised end-to-end (sync + guard + dormant gate).
- improvement-roadmap.md: roadmap step 3 (propagate scaffold→extrends+psc) — extrends ✅.
