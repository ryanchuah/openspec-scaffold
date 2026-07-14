# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (tier-keyed, platform-uniform chain — MEDIUM self→pro behavioral, COMPLEX self→pro→flash lens) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — correctness-audit-meta-hardening SHIPPED (2026-07-14)

OW-15, MEDIUM. Four deltas to the shipped `correctness-audit` capability: liveness (an in-progress
dossier stays an Active `knowledge/questions/INDEX.md` item; charter `status:` marker `in-progress`→
`closed`; remediation programs use a namespace distinct from discovery `WAVE-N` rows); a blind
close-out coverage-gap review (four-marker taxonomy diff; both the blind-taxonomy and evidence-fanout
halves load-bearing); a bounded scope-seeding checklist inlined in the skill (11-group dimension seed +
12 named blind-spot classes; classes 9-12 carried as awareness pointers only — the claims-ledger
mechanism is OW-16, not built here); and a post-close `POST-CLOSE-LEDGER.md` for persistence-touching
changes. Two new guarded `knowledge_lint` detectors (`audit-liveness`, `post-close-ledger-format`),
both gated on the existing format marker so un-adopted repos stay clean. Verify: premise AGREE, pro
behavioral verifier READY with zero defects, 9 orchestrator-authored adversarial fixtures held,
`check.sh` green, zero Sonnet fallback. Decisions: `knowledge/decisions/INDEX.md`; follow-ons:
`knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-14-correctness-audit-meta-hardening/`.

## Prior change — delegated-context-caching SHIPPED (2026-07-14)

OW-8 caching hygiene, SMALL. Shipped A (reshaped the 4 delegated `opencode run` prompt strings —
apply/archive/propose-reviewer/AGENTS.md SMALL-premise — to put per-change variable paths LAST for
DeepSeek prefix-cache credit; markers preserved) + D (codified the variable-last convention as
`delegation-harness.md` §(g); batch-AGENTS.md-edits note added). **B DEFERRED (blocked):**
`OPENCODE_DISABLE_PROJECT_CONFIG` proven (binary+empirical) to also disable `.opencode/agents/`
discovery → would silently swap the executor for a built-in default. **C DROPPED:** premise prompt
only ~7 words truly shared → over-engineering. No spec delta. Verify: premise AGREE, flash verifier
READY zero defects, `check.sh` green, zero Sonnet fallback. Decisions: `knowledge/decisions/INDEX.md`;
follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-14-delegated-context-caching/`.

## Prior change — knowledge-surface-bounding-2 SHIPPED (2026-07-14)

Mechanized two boot-surface bounds that AGENTS.md's prose already states but nothing enforced:
`status_lint.py` gained a C3 check bounding each cap-exempt STATUS.md section (current
state/immediate next action/done/pointers) by a per-heading word budget, and a new
`scripts/boot_surface_lint.py` sums the four mandatory boot-read files against WARN/FAIL byte
thresholds. No spec delta — both mechanize existing canonical AGENTS.md rules, not new ones. A
companion STATUS prune relocated the shipped-but-unpropagated ledger to
`knowledge/reference/pending-downstream-propagation.md`, bringing the boot surface itself under
budget. Verify: self-review PASS, 21 independently authored adversarial/boundary fixtures held,
pro behavioral verifier READY with zero defects, `check.sh` green, zero Sonnet fallback.
Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-14-knowledge-surface-bounding-2/`.

## Immediate next action
No proactive build in flight. OW-15 (correctness-audit-meta-hardening) shipped —
`openspec/changes/archive/2026-07-14-correctness-audit-meta-hardening/`. The wave-2 scaffold-hardening
remainder is **OW-12** (archive mechanization, lowest priority), **OW-16** (product-audit greenfield,
chain-independent — carries OW-15's classes 9-12 awareness pointers + the claims-ledger mechanism),
and OW-11's fuzzy de-bloat residual (`knowledge/questions/skill-debloat-gates-follow-ons.md`). Note:
OW-15's prior "BLOCKED on unshipped OW-5" status (in the old HANDOFF/STATUS) was stale — OW-5
(`correctness-audit`) shipped 2026-07-13; the `OUTSTANDING-WORK.md` tracker line has been corrected.
Single source of the backlog: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.

The **Fable-tier design backlog is closed** (2026-07-11 workflow audit:
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`) — everything remaining is Opus-tier. Earlier
portfolios (the frozen OW-2→3→5→6 batch; OW-1/4/7/9/10/11/14; succession-hardening; day-to-day
tooling A/B/C) are shipped. Downstream propagation of the shipped scaffold changes is
**operator-gated and deferred** — the running ledger now lives in
`knowledge/reference/pending-downstream-propagation.md`.
