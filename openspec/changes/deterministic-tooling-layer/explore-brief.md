# Explore brief + session handoff: deterministic tooling layer (audit prep + agent assistance)

**Type:** explore-brief for the direction gate, doubling as a comprehensive session handoff.
**Created:** 2026-07-02 by a Claude Fable 5 session in `openspec-scaffold` (operator: Ryan).
**Supersedes:** `../extrends/AUDIT-WORKFLOW-HANDOFF.md` — fully absorbed here; the operator can delete it.
**Status:** §6 open items RESOLVED with operator 2026-07-02; direction gate PASSED
(`PREMISE: AGREE`, 2026-07-02 — see `premise-review.md`); propose started at tier **MEDIUM**.

> **For a resuming session:** read AGENTS.md's mandatory set first, then this file. The direction
> gate has already run (`premise-review.md`); §6 needs no re-confirmation. Continue the OpenSpec
> change `deterministic-tooling-layer` from wherever `openspec/changes/deterministic-tooling-layer/`
> left off. All load-bearing evidence is inlined below — the originating session scratchpad
> (`/tmp/claude-1000/...`) is ephemeral and may be gone.

---

## 1. Problem statement

The operator has three goals, established across this session (they supersede the narrower framing
in the old extrends handoff):

1. **Cheap Fable audits.** Another full code audit of extrends by Fable is wanted. Fable tokens are
   expensive, so everything deterministic or cheap-model-doable must happen upfront, and the audit
   context must stay lean. Last time, prep was ~12 LLM sessions running the mechanical
   `~/Projects/prompts/P0–P9` pipeline — pure token-burn on work scripts can do.
2. **Long-run agent assistance.** Provide agents working in extrends/psc-monitor with cheap,
   non-LLM tooling (runnable at session start or mid-session) so they stop wasting tokens/context
   on things static analysis does better.
3. **Fill missing deterministic-workflow categories.** CVE detection was one known miss; the
   session surveyed what else exists (result: §4).

Constraints: both repos are solo, self-hosted, free-tier; tooling is worked by Claude *and*
non-Claude agents (must be agent-neutral); cost of implementation, maintenance, and false-positive
triage must be justified against actual gain — over-engineering is an explicit failure mode.

## 2. Verified facts (the proof base)

**Git/repo archaeology (verified by read-only recon subagent, 2026-07-02):**
- Last comprehensive Fable audit: **2026-06-10**, anchored at extrends commit `268beca`
  (2026-06-11). No later full audit exists (later items are a scoped test-audit ~06-20/25 and a
  strategy reframe `4a29e92` 06-28, not code audits). **217 commits, 52 src files, ~10.5k
  insertions** since the anchor — so the next audit is necessarily near-total; delta-scoping pays
  only from the following cycle.
- The pipeline's nav docs (`docs/00–09`) were **deleted 2026-06-19** (commit `847628d`, message:
  "all code-derivable, mechanical maps — deleted"). Operator's stated reason: no cheap way to
  regenerate them. They exist only in git history at `268beca`.
- **extrends** (~18k src LOC, 42 test files ~39k LOC, SQLAlchemy ≥2.0, 14 ORM models in
  `src/trendscope/models.py`): the ONLY detector anywhere is pytest (pyproject + justfile `test` +
  CI + commit test-gate hook). **No ruff/mypy/bandit/gitleaks/pip-audit config exists.** Ad hoc
  coverage only via `scripts/_audit_coverage_oneoff.py`.
- **psc-monitor** (Python 3.13, FastAPI, **raw psycopg2 — no ORM**, hand-rolled `migrations/*.sql`,
  ~5.8k Python LOC in api/core/pipeline, React 18 + Vite frontend ~18 files, Astro landing):
  **zero lint/type/security tooling**; CI = pytest (with Postgres 16 service) + `npm test` only.
- **Internal precedent, both repos:** the June test-quality audit used a two-layer pattern —
  deterministic scan scripts dumping JSON (`scripts/_audit_*_oneoff.py`, ~1,600 LOC across 6
  scripts in extrends) → LLM judgment pass. In extrends it found **3 real production bugs**
  (fixed: `eb3fc61`, `a3b467b`, `acadfa5`, `8108a77`); remediation COMPLETE 2026-06-25.
  psc-monitor has its own equivalent (`knowledge/research/test-quality-audit/`, `scan/*.json`).
  This proposal generalizes that proven pattern.

**Prompts-pipeline red-team (subagent read all 12 prompt files):**
- "70–85% scriptable" (prior agent's claim) is fair by *row count*, optimistic by *value*:
  scripts-only preserves ~45–55% of output value — "you keep the index, lose the analysis."
- The judgment lives in **P4** (algorithms: "what it computes / what it enforces" — no N/A escape
  valve; prior agent mis-scored it scriptable) and P5 (dataflow narration). **P8** (performance) is
  *more* scriptable than claimed. S1/P9 are pure text transforms that never needed an LLM.

**Tool claims (web-verified 2026-07-02 via fetch_clean.py; sources = each tool's GitHub/PyPI):**
- ALIVE: pyan3 (revived Feb 2026, v2.6.1, `--text` output built for AI agents), opengrep (v1.25.0),
  pyrefly (stable v1.1.1), mutmut (active, incremental cache), osv-scanner, pip-audit, gitleaks
  (v8.30.1, SARIF), sqlfluff (v4.2.2, Postgres dialect), deptry, paracelsus (tedivm), pytest-testmon
  (v2.2.0), blockbuster, flake8-async, schemathesis, pandera, Soda Core, pytest-benchmark, py-spy,
  scalene, memray, hypothesis, eslint/tsc/knip.
- DEAD/REJECTED: **eralchemy** (no SQLAlchemy 2.x; fork eralchemy2 also deprecated → use
  paracelsus), **migra** (author-deprecated), **safety** (login-gated), pytest-picked (stale).
- `alembic check` is built into Alembic ≥1.9 — free schema-drift detection for extrends.
- No off-the-shelf "EXPLAIN-plan regression in CI" tool exists (ecosystem hole; Dexter/PgHero are
  runtime advisors).
- TSAN/ASAN: compiled-code sanitizers, **not applicable** to pure Python. The Python-relevant
  remnant of that category is async blocking-call detection (ruff ASYNC rules + blockbuster).

**Agent-context research (web-verified):**
- 2026 studies (arXiv 2601.20404, 2602.11988) found **auto-generated** AGENTS.md-style orientation
  files *reduce* agent task success ~3% on average; only hand-curated ones help (~+4%). ⇒
  standing generated prose is net-negative; deterministic, factual, **on-demand** output is the
  good delivery shape.
- pytest-testmon is the mature test-impact tool; Serena is the mature LSP-for-agents if symbol
  navigation is ever needed; ast-grep agent integration exists but is early/opt-in.
- **graphify** (github.com/safishamsi/graphify) was assessed and **rejected**: its code-graph core
  is deterministic (tree-sitter + call graph, queryable graph.json/MCP) but it also emits standing
  generated wiki/prose (the harmful shape), it's a 3-month-old single-author dependency (the
  eralchemy rot lesson), and its 75k-stars-in-3-months stat looks inflated. The useful capability
  is covered by boring old tools (pyan3 etc.). Watch, don't adopt.

## 3. Core design decisions (with rationale)

- **D1 — Same analyses, two delivery shapes.** The Fable audit wants them *report-shaped* (run
  once → `output/audit/<date>/` JSON → baseline → diff next time). Everyday agents want them
  *query-shaped* (seconds-fast task-runner targets run on demand). **No standing generated
  prose** — backed by the 2026 studies and by Fable's own first-person account: precomputed
  *structure* (graphs, schema, scope) is high-value/trustworthy because scripts made it; LLM
  *narrations* are what an auditor must distrust anyway (a wrong "what it enforces" line anchors
  the auditor away from the bug). The deleted nav docs lost little audit value; do not rebuild
  them — descriptive artifacts become disposable regenerated-per-audit build outputs.
- **D2 — Three-level prep pyramid for the audit:** free scripts → cheap-model pre-digestion
  (flash/Sonnet clusters + dedupes the detector wall, drafts summaries **labeled as unverified
  claims/leads, never ground truth**) → Fable does judgment only.
- **D3 — Everything check-only; detectors never write.** No `--fix`, no formatters in any shared
  workflow. Rationale: a scheduled/auto-fixer is a second silent writer — it invalidates other
  agents' stale file models (failed or half-applied edits) and poisons "changed since last audit"
  diffs. If auto-format is ever adopted: one-time operator-triggered sweep in a dedicated commit,
  then check-only enforcement; never scheduled.
- **D4 — Data quality is the headline missed category.** Both products ARE their data; every
  existing tool can be green while pipeline output rots. Start with a plain-SQL invariant runner
  (orphans, dupes, nulls, referential integrity, sane ranges) — ~5 deliberate checks per repo,
  grown from incidents; noise stays near zero because each check is intentional. Frameworks
  (pandera/Soda) only if it outgrows plain SQL.
- **D5 — Dead code/duplication/complexity promoted** (operator override of the initial ranking):
  LLM-authored code accumulates orphaned helpers and re-implementations, and ~10.5k lines landed
  since June with no inventory. Delivery: audit-bundle report + ONE triage campaign
  (cheap-model pre-digest → shortlist → operator/Fable rules → vulture whitelist) — **not** a CI
  gate (gates on these metrics cause endless bikeshedding).
- **D6 — First cycle is a full re-audit.** Build bundle → run detectors → triage first-run wall
  ONCE (this produces the tuned configs + baseline) → `git tag audit/<date>` + append
  `knowledge/audit-log.md` → Fable audits with the bundle as index. Delta-scoping pays from cycle 2.
- **D7 — Scaffold is the home.** Shared scripts are scaffold-managed (edited here, synced via the
  existing `sync_scaffold.py` manifest mechanism); per-repo configs/checks/CI wiring are follow-on
  SMALL changes downstream. psc-monitor differences the scripts must tolerate: no ORM (schema via
  migrations-concat/pg_dump, not paracelsus), Makefile not justfile, npm lockfiles.
- **D8 — Agent-consumption contract (how agents use this without overwhelm).** Delivery shape, not
  a new tool: (a) **one discovery surface** — a single task-runner namespace (`just audit-*` /
  `make audit-*`) plus `audit_bundle.py --list` enumerating available checks; agents discover by
  enumerating, never by reading standing docs. The only always-loaded footprint is one AGENTS.md
  pointer line (consistent with the §2 finding that standing generated prose is net-negative).
  (b) **Bounded output contract** — every detector writes full JSON to disk and prints only a
  one-line summary (check name, counts, exit code, artifact path) to stdout; agent context takes
  the summary, the JSON is queried selectively (the artifact-on-disk pattern AGENTS.md already
  mandates). (c) **Tiered drill-down** — exit code → per-check counts → filtered JSON query → raw
  findings; agents descend only where nonzero. (d) **Baseline diffing kills the wall** — after the
  D6 first-cycle triage produces tuned configs + a baseline, agents and audits see *deltas*, not
  the full detector wall; D2's cheap-model pre-digest handles the one remaining wall (audit time).
  (e) **Eager vs. on-demand split (wall-clock, not just context)** — only the fast floor (ruff,
  gitleaks, osv-scanner, deptry — seconds each) is suitable for eager session-start runs; heavy
  checks (pyan3, vulture/jscpd/radon, testmon, schemathesis) are on-demand/audit-time only.
- **D9 — Drift-prevention posture (why this layer won't rot).** Three surfaces: the tooling itself
  is scaffold-managed (existing `sync_scaffold.py --check` + pre-commit guard already detect drift
  — measured at zero drift 2026-07-01 in psc-monitor); generated outputs are disposable per-audit
  build artifacts per D1 (nothing standing to rot; pinned tools fail loudly on the next
  stop-on-first-failure bundle run, never silently); per-repo *prose about* the tooling is covered
  by the separate knowledge-lint change (see `plans/knowledge-lint/`). Tie-in for propose:
  `knowledge/audit-log.md` uses a lintable one-line registry format (like
  `knowledge/decisions/INDEX.md`) so the knowledge linter can check it for free; the format spec is
  in-lined in this change's artifacts (no dependency on the unwritten linter). Taxonomy placement:
  `audit-log.md` is **reference-type** knowledge (a bounded one-line-per-audit registry ledger;
  `knowledge/README.md` gains its entry when this ships) — full audit outputs stay disposable
  under `output/audit/<date>/`, never tracked. Maintenance loop, explicit: when a pinned tool
  breaks or is upgraded, the operator bumps the pin and re-runs the baseline triage to absorb the
  changed findings — tool rot always surfaces as a loud bundle failure, and recovery is a pin bump
  plus re-baseline, never a silent drift.

## 4. Locked tool roster

**Tier 1 — standing hygiene (both repos unless noted):**

| Capability | Tool | Note |
|---|---|---|
| Audit bookkeeping + delta + hotspots | git + DIY `audit_scope.py` | tag `audit/<date>`, `knowledge/audit-log.md`, diff-since-tag, churn×complexity ranking (complexity from radon) |
| Data linting | DIY runner + per-repo `checks/*.sql` | D4 above |
| Migration hygiene | `alembic check` (extrends) / sqlfluff (psc-monitor) | |
| Dependency CVEs | osv-scanner | also covers npm lockfiles; pip-audit dropped as redundant |
| Dependency hygiene | deptry | unused/missing/transitive |
| Secrets | gitleaks | both repos carry live `.env` files |
| Lint floor | ruff | rulesets: correctness + bugbear(B) + bandit-subset(S) + ASYNC + pyupgrade(UP); exact set tuned during baseline triage |
| Frontend floor (psc-monitor) | eslint + tsc, check-only | knip deferred |
| Index coverage | DIY script | static half only — CONFIRMED keep (operator, 2026-07-02); best-effort: raw-SQL "greppability" is optimistic (f-strings/concat evade static extraction), so treat output as leads; extrends needs one test-run SQL capture; audit-time report, not a CI gate |

**Tier 2 — audit-time reports + pilots (not CI gates):**

| Capability | Tool | Note |
|---|---|---|
| Dead code / duplication / complexity | vulture / jscpd / radon | report + one campaign, per D5 |
| Structure snapshots | DIY tree-entry-env script; pyan3 (call graph); paracelsus (extrends ER); migrations-concat or `pg_dump --schema-only` (psc); FastAPI `openapi.json` (free API surface) | disposable per-audit outputs |
| Test impact | pytest-testmon | pilot in extrends first; watch cache vs concurrent agents |
| Async correctness | ruff ASYNC + blockbuster (psc tests) | blocking psycopg2 in FastAPI event loop = likely real bug class |
| API fuzz | schemathesis (psc-monitor) | derives tests from its own OpenAPI schema |

**Killed / deferred:** plan-snapshot EXPLAIN diffing (**operator: too expensive**); graphify; MCP
graph servers (Serena only if agents demonstrably flail at navigation); mypy/pyrefly (adoption
project on untyped code — gradual, later); opengrep, mutmut, hypothesis, py-spy/scalene
(occasional campaigns, not standing); license compliance (solo, non-redistributed); container
scanning (only if Docker starts mattering); repo flatteners / auto-generated orientation docs
(evidence-backed harmful); TSAN (inapplicable).

**Packaging:** scaffold-managed new files ≈ `scripts/audit_bundle.py` (orchestrator:
stop-on-first-failure, resumable, JSON out), `scripts/audit_scope.py`, data-lint runner,
index-coverage script + manifest entries + audit-log/tag convention documented. Binary tools
(gitleaks, osv-scanner) installed from **pinned release versions recorded in the bundle script**;
Python tools pinned in each repo's dev extras. Task-runner targets live per-repo (justfile /
Makefile — not scaffold-managed).

## 5. Proposed change scope

- **In scope (this scaffold change, tier MEDIUM — operator-confirmed 2026-07-02):** the
  scaffold-managed scripts above, manifest additions, the audit-log/tag convention, a short
  AGENTS.md addition documenting the audit workflow + check-only rule.
- **MEDIUM design-carrier acknowledgment (premise-review 🟡1):** MEDIUM emits `tasks.md` only — no
  frozen `design.md`. This brief is therefore the change's design carrier: `tasks.md` MUST be dense
  with design-guidance task descriptions that pull forward D1–D9 (delivery shapes, check-only,
  output contract, pinning, taxonomy placement), and the change's `notes.md` MUST cite this brief
  as authoritative. The apply-executor must not make design-on-the-fly decisions that contradict
  D1–D9.
- **Out of scope:** per-repo configs/`checks/*.sql`/CI wiring (follow-on SMALL changes in each
  downstream repo); running the actual Fable audit (a later operator-driven session); any
  formatter adoption; anything that writes to code.

## 6. Open items — RESOLVED with operator (2026-07-02)

1. **Tier: MEDIUM confirmed.** Propose emits `tasks.md` only (pro-reviewed before freeze);
   acceptance criteria go in the change's `notes.md`; full verify skill applies.
2. **Index-coverage check: KEEP, static-only.** The expensive EXPLAIN-plan half stays killed;
   the static script ships as an audit-time report, not a CI gate.
3. **Downstream sync: DEFERRED for BOTH repos.** No syncs to extrends **or psc-monitor** without
   explicit operator go-ahead (extrends: another agent still active as of 2026-07-02). The
   superseded `../extrends/AUDIT-WORKFLOW-HANDOFF.md` deletion is deferred with it.

## 7. What's next (exact sequence)

1. New session in `openspec-scaffold`: mandatory reads (AGENTS.md → knowledge/STATUS.md →
   questions INDEX Active → relevant decisions), then this brief.
2. Resolve §6 items with the operator.
3. Run the **direction gate** on this brief (explore skill: hardened `opencode run --agent
   openspec-reviewer --model deepseek/deepseek-v4-pro`; verdict → `plans/deterministic-tooling-layer/premise-review.md`;
   DISSENT → AskUserQuestion re-think/re-scope/override).
4. On AGREE/override: `propose deterministic-tooling-layer`. Note MEDIUM propose emits **tasks.md
   only**, pro-reviewed before freeze; acceptance criteria go in the change's `notes.md`.
5. Apply via the standard ladder (deepseek-v4-flash via `opencode run`, Sonnet fallback);
   verify per the verify skill; archive reconciles knowledge/.

## 8. Provenance & caveats

- Session: Claude Fable 5 (1M ctx), 2026-07-02, in openspec-scaffold. Four recon/red-team
  subagents (extrends recon, prompts red-team, tool verification, psc-monitor shape) + two
  landscape researchers (agent-context tooling, category sweep) + one graphify check — all
  read-only, all web research via `scripts/fetch_clean.py`. Search engines mostly bot-walled
  (DuckDuckGo/Mojeek/Ecosia); discovery fell back to Startpage + direct GitHub/PyPI fetches, so
  "what's popular" signals are weaker than "is it alive" signals (which used repo pushed-at dates).
- Repo mutations by this session: ONLY this file (plus `mkdir plans/deterministic-tooling-layer/`).
  Uncommitted. Nothing in extrends/psc-monitor was touched.
- The two arXiv orientation-doc findings were reported by a Sonnet researcher; spot-check them
  before citing beyond this project.
