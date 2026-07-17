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

## Latest change — reconcile-parked-backlog SHIPPED (2026-07-17)

Swept the parked-questions backlog after finding two tracker files were filed stale by their own
change's archive commit; fixed the root cause (the archive step must verify a follow-on was not
already resolved by the very change being archived before filing it) and closed every genuinely-stale
item against an adversarially re-verified evidence list. Also shipped three small mechanical fixes the
sweep surfaced: `freeze_check` bold-emphasis tolerance (still line-anchored), `scaffold_lint`'s
tombstone-derived skill vocabulary (closing a removed-name blind spot structurally), and
`knowledge_lint`'s recursive `plans/` gather (agreeing with `outstanding.py`). Verify: self-review and
an independent behavioral pass both READY; live probes were eyeballed directly (planted nested-plan
fixtures; reverted-then-restored `scaffold_lint.py` to confirm the new test isn't vacuous) rather than
inferred; the system ran clean end to end. Decisions: `knowledge/decisions/INDEX.md`; follow-ons:
`knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-17-reconcile-parked-backlog/`.

## Prior change — split-outstanding-work-skills SHIPPED (2026-07-16)

Split the overloaded `outstanding-work-review` skill in two: renamed to `outstanding-work-scan`
(cheap deterministic gather + untriaged-bucket dedup only) and added `outstanding-work-deep-sweep`
(pull-only, operator-invoked five-category residual prose sweep as parallel subagents), mirroring
the deterministic-check-vs-deep-audit split. Verify: self-review + pro behavioral pass + flash
test-quality lens all READY, simplicity gate PASS; one defect (tombstone written file-form instead
of dir-form) found by orchestrator self-review and fixed inline, confirmed via read-only
`sync_scaffold.py --check`; `check.sh` and `openspec validate --strict` clean. Decisions:
`knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Downstream propagation
to psc-monitor/extrends is operator-gated (`knowledge/reference/pending-downstream-propagation.md`).
Archive: `openspec/changes/archive/2026-07-16-split-outstanding-work-skills/`.

## Prior change — skill-debloat-residual (OW-11 residual) SHIPPED (2026-07-14)

Closed the entire OW-11 residual — the last item on the wave-2 scaffold-hardening backlog, which is
now **empty**. Verify's fuzzy keyword-coverage prose replaced with a deterministic requirement/scenario
enumeration plus a behavioral-evidence coherence note; a new `notes-checkpoint-structure` detector
(`checks.py`) mechanizes the 5-field verify-checkpoint obligation; `freeze_check.py` derives a
`FREEZE: READY|BLOCKED` verdict from a strict reviewer `VERDICT:` token (+ `PREMISE` for proposals),
centralizing freeze policy while the reviewer stays decoupled; explore's dead gallery prose trimmed;
plus two HANDOFF lessons (fixture reconstruction-fidelity/idempotency/exit-code+state guidance) and
the `checks.py --check` cwd-litter fix. Verify: self-review's 4 adversarial fixtures held clean, pro
behavioral pass READY, flash test-quality lens READY, simplicity gate PASS (5 behavior-preserving
cleanups, re-verified); `check.sh` and `scaffold_lint.py` clean; zero Sonnet fallback. Decisions:
`knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-14-skill-debloat-residual/`.

## Immediate next action
No proactive build in flight. `reconcile-parked-backlog` shipped —
`openspec/changes/archive/2026-07-17-reconcile-parked-backlog/` — sweeping the parked
`knowledge/questions/` backlog and root-causing the archive step's own follow-on-filing gap. Two
concrete items are ready for an operator call: the composition-audit ceremony is now **DUE** (both
the archived-change and commit thresholds are crossed — an operator ceremony, not a scaffold change;
the live signal is self-computed, run `facts.py --check outstanding` for the current figures rather
than trusting a number written here); and `openspec/changes/knowledge-lint-gitignored-citation-exempt/`
is already verified and landed (`7f23eda`) and needs only an archive-move.

Per the 2026-07-11 workflow-audit verdict (`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`),
**scaffold process optimization is at diminishing returns**: future work is downstream, not new
scaffold mechanism — chiefly extrends' ~33 open correctness-audit defect classes with zero remediation
shipped. Downstream propagation stays operator-gated — running ledger:
`knowledge/reference/pending-downstream-propagation.md`.
