# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (platform-specific chains; Claude self→pro→flash, OpenCode self→flash) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2.

## Latest change — delegated-agent-safety SHIPPED (2026-07-03)

Delegated-agent data-safety hardened across four scopes: (a) the verify verifier's `bash: allow`
scalar became a destructive-command denylist (catch-all allow) plus a co-primary data-safety
preamble; (b) a sanctioned mid-session handoff file `knowledge/HANDOFF.md` (ephemeral, boot-if-present);
(c) `sync_scaffold.py` stamps a non-manifest `.scaffold-version` provenance beacon; (d) a new-repo
bootstrap checklist reference. Verify outcome: the security pass live-proved the denylist matches
literal command spelling, not command identity — `sed -i`, `cp`, `find -delete`, `/usr/bin/rm`,
`env rm`, and a version-suffixed interpreter all bypassed it. Fix: broadened the enumerated set and
rewrote the framing honestly — a speed-bump, not a semantic wall; the verifier is not truly
filesystem-read-only via bash. Multi-model passes were NOT waived; apply/archive ran on Sonnet per
operator directive. Downstream propagation stays FROZEN. Decisions in `knowledge/decisions/INDEX.md`;
follow-ons in `knowledge/questions/`. Archive: `openspec/changes/archive/2026-07-03-delegated-agent-safety`.

## Prior change — mechanize-invariants SHIPPED (2026-07-02)

A deterministic commit-time scaffold linter, `scripts/scaffold_lint.py`, shipped with five checks
(manifest-completeness, agents-md-structure, config-rules-last, dangling-skill-refs, budget-agreement),
converting prose invariants into machine enforcement. This repo's commit-test gate was armed; a
sync-time hook-wiring warning was added to `sync_scaffold.py`. Verdict: READY. Live smoke — four
seeded probes all triggered correctly and reverted clean; the armed gate blocked a red suite and
passed green; sync warnings behaved. Operator overrides recorded: Sonnet executor by directive
(deepseek not attempted); deepseek verifier passes waived; simplicity gate ran (5 of 7 findings
fixed). No downstream propagation — joins the frozen pending-sync queue. Decisions in
`knowledge/decisions/INDEX.md`; follow-ons in `knowledge/questions/`. Archive:
`openspec/changes/archive/2026-07-02-mechanize-invariants`.

## Prior change — knowledge-lint SHIPPED (2026-07-02)

A two-layer per-repo knowledge-drift detector shipped: `scripts/knowledge_lint.py` (stdlib-only,
detect-only — orphan/duplicate canonical files, retired-path tokens, broadened prose path-citation
resolution, dangling archive pointers, guarded audit-log format) plus a `lint-knowledge` operator-invoked
LLM skill for semantic drift (stale "not-built" claims, intra-doc contradictions, buried gates). The
archive step now also runs the linter and flags (never auto-edits) wider-body drift. Verify: self +
deepseek-v4-pro + deepseek-v4-flash all READY; live-run against the scaffold's own `knowledge/` initially
surfaced heavy false-positive noise, fixed by adding a first-path-segment gate + git-ignore skip
(Sonnet-executed defect fix per operator directive), after which only genuine pre-existing drift
remained — enumerated in `knowledge/questions/`, not corrected here (out of scope). New capability spec
promoted; `knowledge-organization` gained one additive requirement. Downstream propagation stays
**frozen pending operator go-ahead**, joining `deterministic-tooling-layer` in the pending-sync queue.
Decisions in `knowledge/decisions/INDEX.md`; follow-ons in `knowledge/questions/`. Archive:
`openspec/changes/archive/2026-07-02-knowledge-lint`.

## Immediate next action
In flight: the succession-hardening portfolio (direction premise-gated 2026-07-02; changes 1
`mechanize-invariants`, 2 `repair-instruction-surface`, and 3 `delegated-agent-safety` shipped) has
one approved change remaining — `prune-knowledge` (SMALL, portfolio closer) — full scope, operator
decisions, and process requirements in `plans/succession-hardening/HANDOFF-next-session.md`. No other
proactive build is in flight. Separately, scaffold changes await downstream propagation to
**extrends** and **psc-monitor** (run `scripts/sync_scaffold.py <repo>`, then review/commit there):
(1) `premise-review-gate` — `AGENTS.md` + four skill/agent files;
(2) `pro-agent-flash-delegation` (SMALL, 2026-06-26) — new `.opencode/agents/explore-flash.md` plus
`task`-whitelist + nudge edits to `openspec-reviewer`, `openspec-verifier`, and both `archive-executor`
copies, and a `scaffold_manifest.txt` line.
Separately, `deterministic-tooling-layer` (MEDIUM, 2026-07-02), `knowledge-lint` (2026-07-02),
`mechanize-invariants` (MEDIUM, 2026-07-02), `repair-instruction-surface` (SMALL, 2026-07-03 —
verify-skill `SKILL.md` restructure only; its AGENTS.md/config.yaml/knowledge fills are per-repo and
do NOT propagate), and `delegated-agent-safety` (MEDIUM, 2026-07-03 — `.opencode/agents/openspec-verifier.md`,
the `AGENTS.md` Roles shared span, `knowledge/README.md`, `scripts/sync_scaffold.py`,
`scripts/knowledge_lint.py`, and `.claude/skills/openspec-verify-change/SKILL.md`) are all complete
but their downstream propagation is **explicitly frozen pending operator go-ahead**
(another agent was active in extrends during this session) — do not sync until authorized; per-repo
wiring (`audit.toml`, `checks/*.sql`, task-runner targets, dev-extras pins for the audit layer; a first
`lint-knowledge` pass for knowledge-lint) is a further follow-on in each downstream repo once sync is
unblocked.
