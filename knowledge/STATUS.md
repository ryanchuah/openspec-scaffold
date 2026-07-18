# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (tier-keyed, platform-uniform chain — MEDIUM self→pro behavioral, COMPLEX self→pro→flash lens) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed. The propose freeze gate tolerates bold-emphasis
`VERDICT:`/`PREMISE:` markdown while staying line-anchored; `scaffold_lint`'s non-openspec
skill-reference vocabulary is derived from the removal-tombstone manifest rather than a
hand-maintained set; `knowledge_lint`'s `plans/` gather is recursive, agreeing with the `outstanding`
fact and the spec; and the archive step itself must now verify a follow-on was not already resolved
by the very change being archived before filing it.

## Latest change — roll-decisions-index SHIPPED (2026-07-17)

The `knowledge/decisions/INDEX.md` registry only ever grows, and had already crossed the boot-surface
budget once, so this change mechanizes a pressure-triggered rolling window: `INDEX.md` keeps a
byte-budgeted newest tail (default 16,000 bytes, `checks.toml`-overridable) while older entries roll
verbatim to `knowledge/decisions/HISTORY.md` via new `scripts/roll_decisions.py`; `knowledge_lint`
gained the `decisions-index-budget` check naming the remedy, and `boot_surface_lint`'s WARN/FAIL
output now names it too. Verify: self-review found and fixed one real defect (a stray entry-count
mention), the independent behavioral pass returned READY zero-defect, and a simplicity-gate review
passed with one accepted low-severity finding (a microseconds-wide non-atomic write window, fully
git-recoverable). This repo's own registry was rolled — boot surface is back under the default WARN.
Resolves OW-13(b). Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`.
Archive: `openspec/changes/archive/2026-07-17-roll-decisions-index/`.

## Prior change — knowledge-lint-gitignored-citation-exempt SHIPPED (2026-07-17)

`knowledge_lint.py`'s broken-citation check exempted only the single hardcoded `output/`
prefix, so a legitimate citation to any other generated/gitignored path (e.g. psc-monitor's
`deploy/rendered/crontab.txt`) flagged as broken on a clean checkout. Fixed by threading the
existing `is_ignored` git-check-ignore callable into `_check_broken_citations`, skipping any
citation target git actually ignores; the `output/` literal stays as the git-unavailable
fallback so behavior is unchanged when git is absent. Verify: independent Sonnet
premise+behavioral review returned AGREE/CONFIRMED with no defects, and `check.sh` ran green
(new unit test reproduces the psc-monitor scenario end-to-end and fails without the guard).
Decisions: `knowledge/decisions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-17-knowledge-lint-gitignored-citation-exempt/`.

## Prior change — handoff-lint-exempt SHIPPED (2026-07-17)

`knowledge_lint.py` was scanning the mandated `knowledge/HANDOFF.md` mid-session handoff as ordinary
steady-state prose, so its forward references, retired-path tokens, planned archive pointers, and
quoted blocks tripped four check families and turned the commit gate red — making the handoff
un-committable and driving agents to delete it. Fixed by extending the existing `knowledge/research/`
exclusion precedent to this mirror-image case (a forward-looking source, not a backward-looking one),
keyed to the exact `knowledge/HANDOFF.md` path in both `knowledge_lint.py` and
`sync_scaffold.py --check-refs`. Verify: self-review found and fixed one real defect (a
configured-scan-dir leak that could re-arm the trap); the `deepseek/deepseek-v4-pro` behavioral pass
returned READY zero-defect on the fixed tree; live probes on the real tree confirmed a tripping
handoff produces zero findings while `check.sh` stays green, and the identical prose in a non-handoff
file still flags (no over-broad suppression). Decisions: `knowledge/decisions/INDEX.md`; follow-ons:
`knowledge/questions/INDEX.md`. Downstream propagation to psc-monitor/extrends is operator-gated
(`knowledge/reference/pending-downstream-propagation.md`). Archive:
`openspec/changes/archive/2026-07-17-handoff-lint-exempt/`.

## Immediate next action
No proactive build in flight. `roll-decisions-index` shipped —
`openspec/changes/archive/2026-07-17-roll-decisions-index/`. Downstream propagation is **PENDING
again**: this change shipped locally-unpropagated (see
`knowledge/reference/pending-downstream-propagation.md`, "Shipped locally — NOT yet propagated"),
and each downstream repo must run its own `scripts/roll_decisions.py` roll BEFORE its live-tree
`knowledge_lint` gate sees the new `decisions-index-budget` check (psc-monitor's registry is already
well over the new default budget). The composition-audit ceremony remains **DUE** (an operator
ceremony, not a scaffold change; run `facts.py --check outstanding` for current figures rather than
trusting a number written here).

Per the 2026-07-11 workflow-audit verdict (`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`),
**scaffold process optimization is at diminishing returns**: future work is downstream, not new
scaffold mechanism — chiefly extrends' ~33 open correctness-audit defect classes with zero remediation
shipped. Downstream propagation stays operator-gated — running ledger:
`knowledge/reference/pending-downstream-propagation.md`.
