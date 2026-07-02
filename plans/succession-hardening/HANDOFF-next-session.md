# HANDOFF — succession-hardening portfolio continuation

**Type:** transient session handoff (2026-07-02). Delete this file — or fold anything still
relevant into `knowledge/` — once the portfolio closes.
**From:** the orchestrator session that shipped portfolio change 1 (context limit reached).
**To:** the next orchestrator session.

## Boot order for the next agent

1. `AGENTS.md` in full, then its mandatory reads (`knowledge/STATUS.md`, Active section of
   `knowledge/questions/INDEX.md`), with the git-log freshness check.
2. This file.
3. `plans/succession-hardening/explore-brief.md` + `premise-review.md` — the portfolio
   direction, premise-gated `PREMISE: AGREE` (pro, 2026-07-02). The direction does not need
   re-gating; per-change premise obligations still apply per tier.

## Standing constraints (do not violate)

- **Downstream sync is FROZEN** by standing operator hold. Queue awaiting the lift:
  `premise-review-gate`, `pro-agent-flash-delegation`, `deterministic-tooling-layer`,
  `knowledge-lint`, `mechanize-invariants`, `repair-instruction-surface` (verify-skill
  `SKILL.md` restructure only — its AGENTS.md/config.yaml/knowledge fills are per-repo and do
  NOT propagate). Do not run `sync_scaffold.py` against a downstream repo until the operator lifts it.
- **Pushes to remotes are NOT authorized.** All of 2026-07-02's commits are local-only.
  Commits to local `main` in small reviewed checkpoints are fine.
- **No standing autonomy grant:** propose tier + plan and get operator confirmation BEFORE
  executing each change (producing the plan is not gated).
- **Flag every deletion to the operator before committing** (standing preference).

## State

Change 1 of 4 (`mechanize-invariants`, MEDIUM) is SHIPPED and archived
(`openspec/changes/archive/2026-07-02-mechanize-invariants/`): `scripts/scaffold_lint.py`
enforces five previously prose-only invariants (manifest completeness, AGENTS.md anchors,
config rules-block position, dangling skill refs, timeout-budget agreement) via a live-repo
SEAL test in the suite; the commit-test gate is ARMED in this repo; `sync_scaffold.py` now
warns when a target repo lacks the `scaffold_check.py` hook wiring.

Change 2 of 4 (`repair-instruction-surface`, SMALL) is SHIPPED (commit `e4eaa2f`, local `main`,
not pushed; artifacts in `plans/succession-hardening/repair-instruction-surface/`). (a) The verify
skill is now a single `**Steps** 1-18` procedure with the behavioral review as Steps 4-8
(content-preserving; SEAL-guarded). (b) AGENTS.md title/project-context + config.yaml `context:`
first-four-fields state the repo IS the golden source (per-repo, proven non-propagating via a
synthetic-target dry-run). (c) `knowledge/reference/exit-codes.md` added (source-verified). Flash
premise `AGREE`; Sonnet apply-executor (operator directive); orchestrator review + single flash
verifier both READY. The verify-skill restructure joins the frozen sync queue; (b)/(c) are
scaffold-local.

## Remaining portfolio changes (operator-approved direction; execute in order)

### 1. `repair-instruction-surface` (SMALL) — ✅ SHIPPED 2026-07-03 (commit `e4eaa2f`)

Done; see State above. Details/rationale in `plans/succession-hardening/repair-instruction-surface/`
(plan.md, premise-review.md, impl-spec.md). The sub-scope breakdown below is retained for the record.

- (a) Restructure `.claude/skills/openspec-verify-change/SKILL.md` so the mandatory behavioral
  review IS the single numbered procedure. Today it is a blockquote preamble followed by a
  separately numbered "Steps 1–10" checklist; every other skill uses "Steps 1–N" as *the*
  procedure, so smaller models pattern-match onto the checklist and skip the behavioral half.
  Content-preserving: every rule, budget, and severity kept; the scaffold_lint SEAL guards
  budgets/refs mechanically.
- (b) Fill the scaffold's own `AGENTS.md` title/project-context spans so the golden source
  stops presenting as an unfilled `<FILL:>` template and states plainly that it IS the golden
  source. These spans are per-repo and NOT propagated — confirm with
  `sync_scaffold.py --check` against a downstream that the edit produces zero drift effect.
- (c) Optional small `knowledge/reference/` file: the exit-code conventions table
  (audit family 0/2/3; knowledge_lint & sync --check 0/1; status_lint 0/2; test-gate 0/2;
  _convergence verdict-on-stdout).
- Already done — drop from scope: the dangling `openspec-continue-change` reference fix
  shipped with change 1.
- Process: SMALL per AGENTS.md — plan + flash premise pass BEFORE apply delegation; single
  flash verifier pass after; no verify-skill invocation.

### 2. `prune-knowledge` (SMALL) — next up; operator pre-approved AGGRESSIVE pruning

- (a) Fix the drift `python3 scripts/knowledge_lint.py` already flags in this repo's own
  `knowledge/` tree (pre-existing findings incl. stale `ai-docs/` refs in `roadmap.md` and
  `decisions/INDEX.md`, an archive-prefix citation gap).
- (b) Close fully-resolved parked question files (`cap-status-log-follow-ons` and
  `split-open-questions-follow-ons` are recorded as fully resolved; verify each before
  closing; sweep the rest for the same).
- (c) Decide and execute the `openspec-onboard` skill's fate (551 lines re-implementing the
  lifecycle inline — drift risk). Slim hard or delete. If deleting a manifest-listed file:
  the manifest has NO deletion/tombstone mechanism — downstream copies must be deleted
  manually per-repo when the sync freeze lifts; record that in the pending-sync queue note.
- (d) `knowledge_lint.py` `DEFAULT_RETIRED_PATHS` bakes a personal path (`/home/me/`) into
  golden-source defaults — generalize or remove (file is scaffold-managed; the edit
  propagates on next sync).
- (e) Clean stray `plans/` files (`plans/premise-review.md`,
  `plans/pro-agent-flash-delegation.md`) after verifying they're obsolete; decide
  `plans/succession-hardening/` residency when the portfolio closes.
- Related items live in `knowledge/questions/mechanize-invariants-follow-ons.md`.

### 3. `delegated-agent-safety` (MEDIUM)

- (a) Structural fix for the `openspec-verifier` data-safety hazard: the verifier
  (`bash: allow`, `edit: deny`) mutated extrends' production SQLite during a real 2026-06-28
  verify; current mitigation is a per-prompt warning string. The direction gate's explicit
  instruction: explore PERMISSION-LEVEL tightening in the OpenCode permission model
  (external_directory scoping, bash allowlists, a read-only variant) BEFORE settling for a
  mandatory data-safety preamble in `.opencode/agents/openspec-verifier.md`; if prose is the
  best available, record the residual risk honestly rather than presenting it as resolved.
- (b) Sanctioned single-file mid-session handoff convention (extrends improvised three root
  HANDOFF files; bless one — e.g. `knowledge/HANDOFF.md`, boot-read if present, deleted on
  absorption). Touches the AGENTS.md shared span + `knowledge/README.md` taxonomy (both
  scaffold-managed; joins the frozen queue).
- (c) Drift beacon: sync stamps the scaffold commit SHA into the target so staleness is
  visible from the downstream repo without running `--check` from the scaffold.
- (d) New-repo bootstrap checklist as a small `knowledge/reference/` file (dissolved-handbook
  remnant; change 1's hook-wiring warning covers the mechanical half).
- Process: MEDIUM per AGENTS.md — tasks.md only, pro-reviewed to freeze; full verify skill
  (multi-model passes + simplicity gate) unless the operator explicitly waives again.

### 4. Operational queue (operator-gated — do not start unprompted)

- When the operator lifts the sync freeze: `python3 scripts/sync_scaffold.py ../extrends` and
  `../psc-monitor`, review + commit per repo; then per-repo wiring follow-ons (`audit.toml`,
  `checks/*.sql`, `audit-*` task-runner targets, dev-extras pins; a first `lint-knowledge`
  pass in each repo).
- Push to remotes when the operator authorizes.

## Orchestrator model requirement per task (operator asked for this assessment)

**Verdict: an Opus-class orchestrator is sufficient for everything that remains.** The
Fable-level work — open-ended exploration, synthesizing five repo sweeps into a direction,
deciding what NOT to build — is done and frozen into the premise-gated brief. What remains is
execution of an approved plan inside a workflow whose gates (flash/pro premise passes, pro
artifact reviews, multi-model verify, the now-armed deterministic commit gate) exist precisely
to catch orchestrator mistakes.

| Task | Orchestrator | Rationale |
|---|---|---|
| repair-instruction-surface | **Opus — comfortably** | Careful content-preserving editing with review gates; risk is mechanical (guarded by the SEAL) plus reviewer-checked prose fidelity. |
| prune-knowledge | **Opus — comfortably** | Deletion judgment is pre-scoped ("aggressive, flag first"), and the linter enumerates most targets. |
| delegated-agent-safety | **Opus — acceptable; the one to watch** | The design step (permission-model research, honest residual-risk framing) is the most judgment-heavy remaining work. The direction gate has already pinned the trap (prose fix masquerading as mechanism), and the pro reviewer + premise verdict backstop it. Use Fable here only if you want extra assurance on the security-relevant design. |
| downstream propagation + wiring | **Opus — comfortably** (Sonnet-class orchestrator would likely also cope) | Mechanical: run sync, read diffs, commit; wiring is per-repo config following existing docs. |
| a future strategic re-audit (nothing scheduled) | **Fable preferred** | Open-ended synthesis and prioritization without gates to lean on is where the model tier genuinely mattered this session. |

## Session facts a fresh agent won't find in the docs

- Test invocation on this machine is `pytest -q` from the repo root; `python3 -m pytest`
  FAILS (pytest is user-installed for python3.13 only). `scripts/test-cmd` encodes this.
- The commit gate is now live: every `git commit` through Claude Code's Bash tool runs the
  full suite (~2s). A red suite blocks the commit (exit 2). If the scaffold_lint SEAL test is
  what's red, a real invariant was violated — fix the violating file; never loosen the test.
- The `openspec` CLI hung once on `openspec status` (2-minute timeout); retrying with
  `timeout 30 ... < /dev/null` worked. Watch for it.
- Operator directives this session were PER-RUN, not standing: Sonnet apply-executor was
  chosen over deepseek-flash for change 1's implementation and its fix batch; the deepseek
  verifier passes were waived for change 1 (simplicity gate kept). The skills' default
  ladders stand for future changes unless the operator re-directs — ask when in doubt.
- Operator philosophy (also in harness memory, restated here agent-neutrally): mechanism over
  docs — deterministic checks first, agent-readable on-demand reference second, human docs
  last. No maintainer handbook. No repo-#3 init tooling (checklist only).
