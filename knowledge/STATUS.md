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

## Latest change — git-native-commit-gate SHIPPED (2026-07-18)

A git-native `pre-commit` hook (`scripts/githooks/pre-commit`, wired via `core.hooksPath` through new
`scripts/setup-hooks.sh`) now enforces the commit-test gate on every `git commit` regardless of
command spelling or agent harness, closing the prefix-evasion gap (`cd && git commit`,
`git -C … commit`, `env … git commit`) and the Claude-only gap (OpenCode/DeepSeek and
operator-terminal commits were never gated). The existing Claude `PreToolUse` `scripts/test-gate.sh`
now defers (fail-safe) to git-native when it is wired, so a normally-set-up clone runs the gate at
most once per commit; a clone that skipped setup keeps the Claude-only fallback. Verify: the real
git-native hook blocked red commits across every evasion spelling in a throwaway repo, allowed a
`--no-verify` commit (the visible opt-out) and a green commit; `test-gate.sh` correctly deferred when
git-native was active and ran `check.sh` itself under `--no-verify`; this repo now dogfoods
git-native. Independent behavioral and test-quality verifier passes both returned READY zero-defect.
Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-18-git-native-commit-gate/`.

## Prior change — graduate-sast-scanners SHIPPED (2026-07-18)

Semgrep and Bandit graduated as built-in parsed checks in `checks.py` (heavy-tier,
default-disabled, version-recorded-not-gated for sync-safety); `install-tools.sh` restructured
so Go-absence no longer short-circuits pip provisioning for the two Python SAST scanners;
`security-scanners.md` documented the opt-in configuration pattern. Verify: real-tool live
smoke (bandit 1.9.4, semgrep 1.170.0) through the exact runners normalized every finding to
the standard shape; boundary fixtures (empty/missing/null results, missing line keys, non-JSON
stdout) all handled correctly; independent behavioral verifier returned READY zero-defect;
simplicity gate passed. Both scanners absent from `EXPECTED_TOOL_VERSIONS` — version recorded,
never gated. Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`.
Archive: `openspec/changes/archive/2026-07-18-graduate-sast-scanners/`.

## Prior change — roll-decisions-index SHIPPED (2026-07-17)

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

## Immediate next action
No proactive build in flight. `git-native-commit-gate` shipped —
`openspec/changes/archive/2026-07-18-git-native-commit-gate/`. Downstream propagation is **PENDING**
for three unpropagated changes: `roll-decisions-index` (extrends needs its own pre-roll before sync —
psc-monitor's registry is already condensed), `graduate-sast-scanners` (scaffold-managed files
propagate byte-identical; `security-scanners.md` needs a manual per-repo sweep), and
`git-native-commit-gate` (scaffold-managed files propagate byte-identical incl. exec bit; each
downstream must run `bash scripts/setup-hooks.sh` once). See
`knowledge/reference/pending-downstream-propagation.md` for the full ledger and per-change caveats.
The composition-audit ceremony remains **DUE** (an operator ceremony, not a scaffold change; run
`facts.py --check outstanding` for current figures rather than trusting a number written here).

Per the 2026-07-11 workflow-audit verdict (`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`),
**scaffold process optimization is at diminishing returns**: future work is downstream, not new
scaffold mechanism — chiefly extrends' ~33 open correctness-audit defect classes with zero remediation
shipped. Downstream propagation stays operator-gated — running ledger:
`knowledge/reference/pending-downstream-propagation.md`.
