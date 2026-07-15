# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (tier-keyed, platform-uniform chain — MEDIUM self→pro behavioral, COMPLEX self→pro→flash lens) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — skill-debloat-residual (OW-11 residual) SHIPPED (2026-07-14)

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

## Prior change — archive-mechanization (OW-12) SHIPPED (2026-07-14)

OW-12, the last item on the scaffold-hardening backlog. The archive phase's mechanical work — the
change-dir move and ADDED/REMOVED/RENAMED spec-delta promotion — is now deterministic:
`scripts/apply_delta_spec.py` (plan-all-in-memory, write-all-or-nothing, any anomaly halts and
writes nothing) and `scripts/archive_move.py` (conflict-guarded move). The LLM now does only
MODIFIED merges and doc reconciliation. Dogfooded on its own archive: the promoter created
`openspec/specs/archive-mechanization/spec.md` from this change's own all-ADDED delta, zero
anomalies. Verify: self-review's 16 adversarial fixtures caught 3 real product defects (a
new-capability self-collision gap, blank-line drift, and a trailing-section reorder that would have
corrupted a canonical spec), fixed by a fresh flash executor with zero Sonnet fallback; pro
behavioral pass READY, flash test-quality lens READY, simplicity gate PASS; tests pass and the
system ran clean. Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`.
Archive: `openspec/changes/archive/2026-07-14-archive-mechanization/`.

## Prior change — product-audit-skill (OW-16) SHIPPED (2026-07-14)

New operator-invoked, pull-only `product-audit` skill (new capability) plus one guarded
`knowledge_lint` claims-ledger-staleness detector (`knowledge-lint` MODIFIED). Operationalizes OW-15's
carried-forward classes 9–12: the claims-ledger convention (promise → delivering code surface → proving
check), entitlement-state reachability, severity-taxonomy completeness, and source-class labeling for
durable web claims. Findings route into the existing finding-closure ratchet, no new machinery;
single-session design, no liveness obligation. Verify: premise AGREE throughout; self-review, adversarial
fixtures, and the flash test-quality lens all READY zero defects; the pro-tier behavioral verifier
emitted no verdict (operational failure) so a Sonnet fallback completed that pass, also READY; simplicity
gate clean; `check.sh` and live-tree lint green; zero Sonnet fallback on apply. Decisions:
`knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-14-product-audit-skill/`.

## Immediate next action
No proactive build in flight. `skill-debloat-residual` (OW-11 residual) shipped —
`openspec/changes/archive/2026-07-14-skill-debloat-residual/` — closing the entire wave-2
scaffold-hardening backlog: it is now **empty**. Single source of the (now-empty) backlog:
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.

Per the 2026-07-11 workflow-audit verdict (`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`),
**scaffold process optimization is at diminishing returns**: future work is downstream, not new
scaffold mechanism — chiefly extrends' ~33 open correctness-audit defect classes with zero remediation
shipped. Downstream propagation of the shipped scaffold backlog was **executed 2026-07-15**
(extrends + psc-monitor now scaffold-content-current, local/unpushed); future scaffold changes stay
operator-gated — running ledger: `knowledge/reference/pending-downstream-propagation.md`.
