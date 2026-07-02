# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (platform-specific chains; Claude self→pro→flash, OpenCode self→flash) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2.


## Latest change — deterministic-tooling-layer SHIPPED (2026-07-02)

A scaffold-managed deterministic audit layer shipped: `audit_bundle.py` (check orchestrator),
`audit_scope.py` (git-archaeology delta scoping + `tag` anchor), `data_lint.py` (plain-SQL
data-invariant runner, server-enforced read-only), and `index_coverage.py` (static index-coverage
leads) — check-only, JSON-to-disk, agent-neutral, stdlib-only, sharing a 0/2/3 exit-code triple
(clean/findings/infra-failure). `AGENTS.md` gained a "Deterministic audit tooling" section and
`knowledge/README.md` an audit-log taxonomy entry. Verify: self → deepseek-v4-pro → deepseek-v4-flash
→ simplicity/quality gate → flash re-run all READY, full suite green throughout; live runs against
real ruff/radon/vulture output and real psc-monitor migrations behaved correctly (correct baseline
deltas, honest complexity/duplication findings, plausible index-coverage leads). Several defects found
during self-review and the quality gate were fixed and re-verified; pro and flash passes found zero.
No delta specs (tasks-only). Downstream propagation (extrends, psc-monitor) is frozen pending explicit
operator go-ahead. Decisions in `knowledge/decisions/INDEX.md`; follow-ons in `knowledge/questions/`.
Archive: `openspec/changes/archive/2026-07-02-deterministic-tooling-layer`.

## Prior change — premise-review-gate SHIPPED (2026-06-21)

A two-altitude pre-implementation premise-review gate shipped, vetting a change's direction
(problem/root-cause/solution) before implementation: a pro direction gate on load-bearing explore
output (all tiers) and change-itself checks (flash for SMALL plans, folded into pro proposal review
for MEDIUM/COMPLEX). The existing `openspec-reviewer` agent gained an orthogonal `PREMISE: AGREE|DISSENT`
verdict written default-to-dissent, with `DISSENT` surfaced to the operator and never silently
auto-resolved; `proposal.md` freeze now requires zero 🔴 AND `PREMISE: AGREE`. Verify: live behavioral
smoke — a real deepseek-v4-flash premise pass against a deliberately symptom-level plan — correctly
returned `PREMISE: DISSENT` with cited root-cause concerns, confirming the gate's core dissent
capability. Two defects found and fixed (reviewer-agent premise section rendered inside a code fence;
stale acknowledgement count). New capability spec promoted; reviewer-budget now covers three invocation
paths. Decisions in `knowledge/decisions/INDEX.md`; follow-ons in `knowledge/questions/`. Archive:
`openspec/changes/archive/2026-06-21-premise-review-gate`.

## Prior change — rename-memory-to-knowledge SHIPPED (2026-06-19)

Tracked project-knowledge folder renamed `memory/` → `knowledge/` across all three repos (scaffold,
extrends, psc-monitor) — folder, both capability specs (`knowledge-organization` 4 requirements,
`scaffold-sync-mechanism` 1 requirement), sync/lint mechanism (`sync_scaffold.py` incl.
`_AIDOC_PATH_RE`→`_KNOWLEDGE_PATH_RE`, `status_lint.py`, manifest), both archive-executor bodies,
skills, AGENTS.md, config — resolving the collision with Claude Code's harness-native
`~/.claude/.../memory/`. Verify: self + deepseek-v4-pro + deepseek-v4-flash verifier passes all
READY, zero defects; sync --check/--check-refs/status_lint green in all three repos; folder-vs-feature
exceptions (harness path, historical decisions essence, agent-memory URL) confirmed intact. Two MODIFIED
delta specs promoted at archive. Decisions in `knowledge/decisions/INDEX.md`; follow-ons in
`knowledge/questions/`. Archive: `openspec/changes/archive/2026-06-19-rename-memory-to-knowledge`.



## Immediate next action
No proactive build in flight. Two scaffold changes await downstream propagation to **extrends** and
**psc-monitor** (run `scripts/sync_scaffold.py <repo>`, then review/commit there):
(1) `premise-review-gate` — `AGENTS.md` + four skill/agent files;
(2) `pro-agent-flash-delegation` (SMALL, 2026-06-26) — new `.opencode/agents/explore-flash.md` plus
`task`-whitelist + nudge edits to `openspec-reviewer`, `openspec-verifier`, and both `archive-executor`
copies, and a `scaffold_manifest.txt` line.
Separately, `deterministic-tooling-layer` (MEDIUM, 2026-07-02) is complete but its downstream
propagation is **explicitly frozen pending operator go-ahead** (another agent was active in extrends
during this session) — do not sync until authorized; per-repo wiring (`audit.toml`, `checks/*.sql`,
task-runner targets, dev-extras pins) is a further follow-on SMALL change in each downstream repo once
sync is unblocked.
