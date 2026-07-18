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

## Latest change — security-audit skill graduated (OW-17) SHIPPED (2026-07-18)

Graduated the reusable `security-audit` skill from psc-monitor's AP-1 proving run (run-first,
graduate-after — the OW-16 path). Ships a normative spec `openspec/specs/security-audit/spec.md`
(8 requirements) + an operator-invoked, pull-only skill: a lane-split adversarial audit — charter
(lane select + attacker persona + secrets-exclusion) → front-loaded scanner floor
(SAST-is-a-floor-not-a-finder) → per-lane adversarial passes (empirical-probe-first;
confirm-the-negatives are the clean-lane deliverable) → delegated flash-refuter (money/abuse races
surfaced, not auto-fixed) → cross-lane completeness critic →
`SECURITY: CLEAN|FINDINGS-ROUTED|ESCALATE` → finding-closure ratchet, with multi-session liveness +
deploy-time edge deferral. First scaffold skill owning the classic vuln classes. The deterministic
half (bandit/semgrep) shipped earlier as `graduate-sast-scanners`. NOT Fable (guardrailed). Verify:
all deterministic gates green + orchestrator self-review. Record:
`openspec/changes/archive/2026-07-18-graduate-security-audit-skill/`.

## Prior change — detect-truncated-stream SHIPPED (2026-07-18)

A `detect_truncated_stream()` helper in `scripts/opencode_delegate.py` catches
silently-truncated `opencode run` streams — the provider returns an empty completion,
opencode treats no-assistant-output as a clean end-of-stream and exits 0, and the wrapper
was classifying the run `ok`. The detector counts top-level `step_start` vs `step_finish`
across the JSONL output; an imbalance produces a new `truncated-stream` classification that
outranks `marker-missing`. No failure-ladder or ledger-schema changes. Verify: flash premise
AGREE, flash verifier READY zero-defect (Chinese-language verdict block was a marker-literal
language-drift artifact, not a real failure — stream balanced, substance READY); orchestrator
independently confirmed the detector flags the actual incident file that originally slipped
through. Full suite green. Decisions: `knowledge/decisions/INDEX.md`; follow-ons:
`knowledge/questions/INDEX.md`. Record: `plans/archive/detect-truncated-stream/`.

## Prior change — custom-checks-family-fix SHIPPED (2026-07-18)

`_custom_checks()` in `scripts/checks.py` now honors a normalized, gating-safe `family=` key so
`[checks.custom.*]` entries can register fact-family (preflight-exempt, graceful-degrade) checks; an
invalid/typo value falls back to `check` (gated), never silently `fact`. Docstring and regression
tests updated. Unblocks downstream app-specific fact snapshots (e.g. psc-monitor route-authz) via config
alone, no standalone script needed. Verify: flash premise pass returned AGREE, flash verifier
returned READY zero-defect, full suite green. Decisions: `knowledge/decisions/INDEX.md`; follow-ons:
`knowledge/questions/INDEX.md`. Record: `plans/archive/custom-checks-family-fix/`.

## Immediate next action
No proactive build in flight. `security-audit` skill graduated (OW-17) — archived
`openspec/changes/archive/2026-07-18-graduate-security-audit-skill/`, committed to scaffold `main`
locally (unpushed). Downstream propagation is **PENDING** for one change:
`graduate-security-audit-skill` (skill `SKILL.md` + `scaffold_manifest.txt` propagate byte-identical
and additive; the normative spec `openspec/specs/security-audit/spec.md`, the `security-scanners.md`
header fix, and the OW-17 tracker entry are scaffold-only / per-repo knowledge and are NOT
auto-propagated — matching the product-audit/composition-audit precedent, where the skill ships
downstream and its spec stays in the scaffold, `--check-refs` still green; no mandatory per-repo
step). The five prior changes (`roll-decisions-index`, `graduate-sast-scanners`,
`git-native-commit-gate`, `custom-checks-family-fix`, `detect-truncated-stream`) were propagated in
the 2026-07-18 frontier (both downstreams at beacon `36adc01`, commit `2c5e6b2`).
See `knowledge/reference/pending-downstream-propagation.md` for the full ledger and per-change
caveats.
The composition-audit ceremony remains **DUE** (an operator ceremony, not a scaffold change; run
`facts.py --check outstanding` for current figures rather than trusting a number written here).

Per the 2026-07-11 workflow-audit verdict (`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`),
**scaffold process optimization is at diminishing returns**: future work is downstream, not new
scaffold mechanism — chiefly extrends' ~33 open correctness-audit defect classes with zero remediation
shipped. Downstream propagation stays operator-gated — running ledger:
`knowledge/reference/pending-downstream-propagation.md`.
