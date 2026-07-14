# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (tier-keyed, platform-uniform chain — MEDIUM self→pro behavioral, COMPLEX self→pro→flash lens) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — verify-adversarial-fixtures SHIPPED (2026-07-14)

Promoted the carried-forward verify lesson (an executor's green tests passed over a real
`spec-delta-structure` detector false-negative on multi-section deltas; ratchet
`detector-statemachine-boundary-flush`) into the durable verify surface: extended
`config.yaml` `rules.verify` step (2)'s "green is necessary but NOT sufficient" clause so the
self-review MUST author its OWN adversarial/boundary fixtures for logic-bearing diffs, plus a
new operational subsection + Step 5 pointer in the verify skill. Single-source: config owns the
rule, skill cites it; no spec delta (self-review content isn't owned by `verify-multimodel-gate`).
Verify: self-review PASS → pro behavioral verifier READY, zero defects; `check.sh` green; the
obligation correctly assessed N/A on this very diff (pure-prose exemption dogfooded). Decisions:
`knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Downstream
propagation is operator-gated and deferred. Archive:
`openspec/changes/archive/2026-07-14-verify-adversarial-fixtures/`.

## Prior change — skill-debloat-gates (OW-11 mechanized gates) SHIPPED (2026-07-14)

Shipped OW-11's mechanized half (MEDIUM, scoped — the fuzzy de-bloat half deferred to a residual
follow-on): a `spec-delta-structure` detector in `checks.py` that structurally validates every open
change's spec deltas by directory presence, closing the `medium-change-spec-delta-unvalidated`
ratchet (`openspec validate` is proposal.md-gated and never saw MEDIUM changes' deltas); a
`model-id-agreement` lint in `scaffold_lint.py` guarding sanctioned deepseek model-id spellings;
concurrent-launch prose for the two COMPLEX verifier passes; and an explore→propose slug near-match
warning. Promoted two spec deltas (`defect-prevention-detectors`, `verify-multimodel-gate`); both
validate `--strict` clean. Verify: self-review caught and re-delegated a fix for a real detector
false-negative (a multi-section scenario-check gap); pro behavioral pass READY, zero defects;
simplicity gate landed four behavior-preserving cleanups; `check.sh` green; zero Sonnet fallback.
Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-14-skill-debloat-gates/`.

## Prior change — apply-throughput-resume SHIPPED (2026-07-14)

Shipped green-path targeted-test cadence in both apply-executor bodies (byte-synced): per-task
scope-narrowed check using the same test tool, then the full documented suite once before
completion — replacing the old unconditional full-suite-per-task. Added a four-point
fresh-executor resume contract to the apply skill's failure ladder (skip `[x]` tasks, resume at
first `[ ]`, reconcile the in-flight task, carry distilled state). Promoted a MODIFIED
apply-convergence-guard delta: scope-narrowing the same tool is permitted; the full suite gates
before completion; two new scenarios. Verify: self-review PASS → pro behavioral READY; check.sh
green. Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`.
Archive: `openspec/changes/archive/2026-07-14-apply-throughput-resume/`.

## Immediate next action
No proactive build in flight beyond the change being worked. The wave-2 scaffold-hardening remainder
is **OW-8 → OW-13 → OW-12** (recommended order; `OW-13 = knowledge-surface-bounding-2`, in flight
this session), plus **OW-15** (BLOCKED on unshipped OW-5) and **OW-16** (chain-independent
greenfield). OW-11's fuzzy de-bloat half is a parked residual follow-on
(`knowledge/questions/skill-debloat-gates-follow-ons.md`). Single source of the backlog:
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.

The **Fable-tier design backlog is closed** (2026-07-11 workflow audit:
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`) — everything remaining is Opus-tier. Earlier
portfolios (the frozen OW-2→3→5→6 batch; OW-1/4/7/9/10/11/14; succession-hardening; day-to-day
tooling A/B/C) are shipped. Downstream propagation of the shipped scaffold changes is
**operator-gated and deferred** — the running ledger now lives in
`knowledge/reference/pending-downstream-propagation.md`.
