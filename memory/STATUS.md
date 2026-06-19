# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-fast-track agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (platform-specific chains; Claude self→pro→flash, OpenCode self→flash) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `memory/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `memory/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `memory/lessons.md` §2.


## Latest change — restructure-project-knowledge SHIPPED (2026-06-19)

Project knowledge restructured: `ai-docs/` → `memory/` with a universal taxonomy (knowledge types,
classification rule, one home per type), bounded boot reads, and a single archive. `STATUS.md` moved to
`memory/STATUS.md`; `decisions.md` → `memory/decisions/INDEX.md` (registry format, pointer-or-inline entries);
`open-questions.md` + `parked-follow-ons.md` → `memory/questions/` (Active blockers / Parked pointers).
Append-only growth capped; second archive (`ai-docs/archive/status-log.md`) retired. `sync_scaffold.py`
gained config `rules:` partial-sync; `status_lint.py` rewritten for the registry decisions check; both
archive-executor bodies rewritten to target `memory/` paths. extrends + psc-monitor migrated — `docs/`,
`plans/`, and `tmp_*.md` deleted with not-in-code knowledge rescued per design checklist D-H. Verify: all
tasks checked off; acceptance criteria met (suite green, sync/check/refs/lint clean in all 3 repos).
Decisions in `memory/decisions/INDEX.md`; follow-ons in `memory/questions/`. Archive:
`openspec/changes/archive/2026-06-19-restructure-project-knowledge`.

## Prior change — add-status-lint SHIPPED (2026-06-18)

A stdlib `scripts/status_lint.py` gate shipped enforcing the forward-only state-file bounds from
AGENTS.md §"State, write discipline, and the archive-as-handoff rule": `memory/STATUS.md`'s 3-entry cap + ≤150-word change-entry budget, and
`memory/decisions/INDEX.md`'s `**Date:**`/`**Status:**` fields + ≤300-word change-record budget — with a
`--since=2026-06-18` backfill-safe cutoff (discovered when the initial date-free spec flagged 12
legacy entries). Wired into both archive-executor bodies as the `#### 3d` lint step and into the
archive skill as the primary's pre-commit gate. Propagated via `sync_scaffold.py` to extrends +
psc-monitor (`--check`/`--check-refs` green). Verify: self + pro + flash verifier passes all READY,
zero defects; linter correctly detects the scaffold's over-budget STATUS entry (Phase B cleanup
tracked in `memory/questions/INDEX.md`). Decisions in `memory/decisions/INDEX.md`; archive:
`openspec/changes/archive/2026-06-18-add-status-lint`.

## Prior change — lean-boot-context SHIPPED (2026-06-18)

State-file bounding rules shipped + enforced at archive; psc-monitor appendix relocated to on-demand
ai-docs/ files, slimming AGENTS.md from 707 to 321 lines. P3: three new state-bounding conventions
(≤150-word STATUS entries, decisions Date/Status + ≤300-word cap, open-questions parking+pointer-stub
rule) live in AGENTS.md §"State, write discipline, and the archive-as-handoff rule" and enforced at archive by both archive-executor
bodies — forward-only, no risky retroactive summarization. P2: psc-monitor's 412-line appendix
verbatim-relocated to 5 ai-docs/ files (schema, API, layout, ops-runbook, project-reference) with an
On-demand references table; every citation repointed; no load-bearing constraint lost. Sync guard
bumped 300→350 to fit lean repos after rule propagation. Verify: primary self-review found 2 defects
(test regression, P2 content loss) → fixed; pro + flash verifier passes both READY, zero defects;
all scaffold tests green; all four convergence/refs gates green. Decisions in `memory/decisions/INDEX.md`;
follow-ons split by horizon (active → `memory/questions/INDEX.md`, parked → Parked section of `memory/questions/`). Archive:
openspec/changes/archive/2026-06-18-lean-boot-context.


## Immediate next action
No proactive build in flight. `restructure-project-knowledge` shipped; `memory/STATUS.md`, `memory/decisions/INDEX.md`,
and `memory/questions/` are now the state-file targets; the dual archive is retired. The add-status-lint
Phase B cleanup is subsumed — `status_lint.py` exits clean in all three repos. The one forward-looking
follow-on (growth-trigger auto-splitter) is parked in `memory/questions/INDEX.md`. All three repos'
`restructure-knowledge`/scaffold branches are local/unpushed — push + downstream merges await operator
go-ahead. Process note for concurrent applies: give each session its own `git worktree`.
