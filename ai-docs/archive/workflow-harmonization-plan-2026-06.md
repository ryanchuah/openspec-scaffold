# Plan — harmonize workflows & rules across scaffold ↔ extrends ↔ psc-monitor

> **Goal (operator, 2026-06-14):** extrends, openspec-scaffold, and psc-monitor end up **in sync
> on workflows and rules**. The scaffold is the golden source; it is edited to embody the canonical
> model, and the other two converge to it. This supersedes the psc-monitor-only migration plan
> (`psc-monitor/tmp_plan_openspec-migration.md`), which is folded in as §4.
>
> **Status:** ✅ HARMONIZATION DONE (2026-06-14) — scaffold + extrends + psc-monitor share
> byte-identical AGENTS.md workflow sections + `ai-docs/fast-track-workflow.md` (commits scaffold
> `3916b96`, extrends `4a8d248`, psc-monitor `cdc0947`). This doc is now the standing design record;
> subsequent shared-rule changes are logged under §0 below.

---

## 0. Post-harmonization update log

Once the three repos are in sync, every change to a shared workflow rule must land in **all three**
(scaffold golden source first, then extrends + psc-monitor) to avoid drift, and is logged here.

- **2026-06-14 — Mandatory re-review after a 🔴 fix** (`.claude/skills/openspec-propose/SKILL.md`,
  both the Claude-CLI and OpenCode branches). The propose review loop already *structurally* required
  re-review (the only freeze path is "no 🔴"), but the Claude branch only said "go back to step 1" and
  the OpenCode branch only said "re-review". Both now state it explicitly: **a fix that clears a 🔴 is
  never self-certified; the artifact may be frozen only by a fresh review round that returns zero 🔴.**
  Committed: scaffold `cbe71e7`, extrends `2788838`, psc-monitor `9f51d27` (all unpushed).
  - *Open follow-up:* the per-repo duplication this required is exactly the pain the
    **single-source-of-truth scaffold** investigation (below / separate change) aims to remove.

---

## 1. Operator decisions locked in

- **Tiers → STANDING in AGENTS.md** (extrends's model) for all three. Tiers are always in effect;
  no fast-track gate on tiering.
- **Fast-track = AUTONOMY-only, opt-in, DORMANT everywhere (Option A, all repos).** All three get
  `ai-docs/fast-track-workflow.md` (the autonomy override mechanism) + an AGENTS.md "Fast-track
  override" pointer, but **no repo carries an active standing grant** — the operator opts in
  per-session. (This supersedes psc-monitor's prior standing autonomy grant; psc-monitor becomes
  phase-gated like the others.)
- **GLM stays a listed agent family** ("OpenCode/DeepSeek/GLM") in all three.
- **Merge-authorization** (squash-merge green queue PRs, report each) is a *separate* working-process
  rule, scoped per-repo to a named queue — preserved for psc-monitor (queue = `plans/open-issues.md`),
  and present generically in the canonical working-process. NOT part of fast-track.

## 2. The canonical model (what "in sync" means)

The **shared AGENTS.md workflow sections** + **`ai-docs/fast-track-workflow.md`** + the **generic
`ai-docs/` templates** are identical across all three repos. Only genuinely project-specific content
differs: AGENTS.md `## Project context` / hard-constraints / the technical-reference body;
`openspec/config.yaml` `context:`; `STATUS.md`; `ai-docs/decisions.md` + `open-questions.md` +
`improvement-roadmap.md` *content* (the templates/headers match; the entries are per-project).

**Canonical AGENTS.md workflow sections** = the current scaffold AGENTS.md, with these edits
(full verbatim in **Appendix CANON-1**):
1. Cross-agent block: agent families → "OpenCode/DeepSeek/GLM".
2. OpenSpec workflow: keep the harness-neutral "skill mechanism" wording + the fixed glob
   `.claude/skills/openspec-*/SKILL.md`; **rewrite the Fast-track override blockquote** (not just
   trim "(tiered)") — it now describes the autonomy override only and notes "Tiering, below, is
   standing and applies regardless."
3. **Insert a standing `## Change tiers` section** (SMALL/MEDIUM/COMPLEX) after `## OpenSpec workflow`.
4. Working process: add the "**Authored deliverables go only to the standard agent-neutral dirs**"
   bullet (generalized — no project-specific dir names).
5. Web research: add rule **(d)** "Never call WebSearch from the main thread; route research through
   subagents using `scripts/fetch_clean.py`."
6. **(U1)** Cross-agent ban narrowed: `.claude/` → `.claude/settings.local.json` — fixes the current
   scaffold's internal contradiction (it bans `.claude/` broadly, then the Exception block relies on
   `.claude/skills/` + `.claude/agents/`). Now the ban targets only harness-private local settings.
7. **(U2)** Exception block gains: "(A tracked, hook-free `.claude/settings.json` permissions file is
   also fine.)" — explicitly permits the shared tracked permissions file.
8. **(U3)** `## Roles` gains the **archive-executor** bullet (the scaffold's current Roles omits it,
   though its State section already delegates to a deepseek-v4-pro archive-executor — this closes that
   internal gap; extrends's Roles already has it).
> **Note:** CANON-2 (fast-track) also elevates "Pushes to `main` still require explicit operator
> authorization" into its Guardrails — a tightening, already a rule in AGENTS.md working-process.
> **Golden-source discipline:** edits 6–8 change the golden source's wording; each fixes a documented
> internal inconsistency and is source-traceable to the Exception block / State section it reconciles.

**Canonical `ai-docs/fast-track-workflow.md`** = the current scaffold file **slimmed to autonomy-only**
(tier definitions removed — they live in AGENTS.md now), no active grant (full verbatim in
**Appendix CANON-2**).

### Verified delta table (resolution column = canonical)
| # | Item | scaffold now | extrends now | psc-monitor now | Canonical → who changes |
|---|---|---|---|---|---|
| T | Change tiers | none (opt-in) | standing ✅ | none | **standing in AGENTS.md** → scaffold +psc add |
| F | fast-track file | has (tiers+autonomy) | missing | none | **autonomy-only, dormant** → scaffold slims; extrends+psc add |
| D1 | skill glob | `openspec-*/` ✅ | `openspec-*-change/` ✗ | n/a | scaffold's → **extrends fixes** |
| D2 | skill invocation | neutral ✅ | "Skill tool" ✗ | n/a | neutral → **extrends fixes** |
| D3 | web rule (d) | absent | present ✅ | (in draft) | add (d) → **scaffold adds** |
| D4 | archive reconciliation (State §) | archive-executor ✅ | "fresh session" ✗ (contradicts own Roles) | n/a | archive-executor → **extrends fixes** |
| D5 | resume-staleness preamble line | present ✅ | absent ✗ | n/a | present → **extrends adds** |
| D6 | working-process bullets | fuller superset ✅ | missing several | n/a | superset → **extrends adds the 6 missing**; scaffold adds the 1 from extrends |
| D7 | GLM family | absent | present | absent | **present** → scaffold + psc add |

(D6 missing-in-extrends bullets: stop-on-first-failure; "don't fan out cohesive/dependency-laden work";
commit-to-main/standing-merge-auth; guard-destructive-and-external; mind-data-scale;
one-canonical-file-per-category. Extrends's unique bullet "authored-deliverables-only-standard-dirs"
is promoted INTO the canonical, so the scaffold gains it.)

---

## 3. Process & sequencing

Each repo is its own git repo; edits go through the standard loop: **plan → deepseek-v4-pro review →
operator approval → deepseek-v4-flash apply (sliced) → orchestrator reviews the diff from disk →
commit to `main` (push only on operator go-ahead).** Golden-source-edit discipline applies to ALL
three now (every edit source-traceable; agent-neutral; respect deliberate prior decisions — read the
relevant commit/why before overwriting).

**Sequence:**
1. **Scaffold first** — establish the canonical model in the golden source (Appendices CANON-1/2 +
   §2 edits). Reviewed, applied, orchestrator-reviewed, committed. *This locks the canonical text.*
2. **Extrends convergence** (§5) — bring extrends to the canonical (D1–D7 fixes + fast-track file).
3. **psc-monitor migration** (§4) — the full OpenSpec adoption, with its AGENTS.md workflow block =
   the canonical text, fast-track dormant.

> **opencode sandbox note:** each repo's deepseek review/apply runs sandboxed to that repo and cannot
> read the others. So the canonical text (CANON-1/2) is **embedded verbatim** in each per-repo apply
> brief; the reviewer/applier never needs to read a sibling repo. (Per `opencode-delegation-notes`.)

**Pre-edit history check (golden-source discipline):** before applying §2 to the scaffold, read the
git log/commit body for the scaffold's fast-track-workflow.md and AGENTS.md "OpenSpec workflow"
section to confirm the "tiers opt-in via fast-track" arrangement wasn't a deliberate decision with a
rationale that the operator's new directive would silently break. Record the model change (tiers →
standing) as an `ai-docs/decisions.md` entry in the scaffold.

---

## 4. psc-monitor migration (folds in `tmp_plan_openspec-migration.md`, with these deltas)

The existing `psc-monitor/tmp_plan_openspec-migration.md` (deepseek-reviewed, PASS-WITH-NITS,
incorporated) stands, with these **alignments to the canonical model**:
- **AGENTS.md new workflow block** = Appendix CANON-1 verbatim (replaces the bespoke block drafted in
  that plan's Appendix B.1). The technical-reference merge (B.2/B.3/B.4) is unchanged.
- **`ai-docs/fast-track-workflow.md`** = Appendix CANON-2 verbatim, **DORMANT — drop the
  Appendix-F standing-grant note** (Option A). The autonomy-preference memory is recorded only as
  context in `ai-docs/decisions.md` (review-workflow entry already covers review autonomy), NOT as an
  active grant.
- **Merge-auth** stays in the working-process (canonical bullet), scoped to `plans/open-issues.md`.
- **GLM** included in the cross-agent family list (canonical).
- **Sudo guard preserved:** CANON-1's working-process has no top-level "never sudo" rule, but
  psc-monitor's `## Do not do` section (KEPT verbatim by B.2) already carries *"Do not run `sudo`
  commands — ask the user to run them."* So the guard survives the CANON-1 swap. (No action needed;
  noted to close review M3.)
- **Apply-brief must be explicit (review N5):** the §4 apply brief states *"the AGENTS.md workflow
  block = CANON-1 from THIS brief; this OVERRIDES the psc migration plan's Appendix B.1, ⟂D5, and
  Appendix F (Option A — no standing grant)."* so the applier doesn't implement the superseded B.1.
- All other phases (machinery copy, openspec skeleton, STATUS.md, decisions.md, archive prompts/+
  remove-legacy-hash, memory-store deletion, bookkeeping) unchanged.

## 5. Extrends convergence (WHOLESALE span-replace → byte-identical shared sections)

> **Method change (per review point 6 + R1–R7):** surgical FIND/REPLACE would leave residual wording
> drift (R1 "DB scans" vs "data scans"; R2 "pipeline ran clean" vs "the system ran clean"; R3 MEDIUM
> tier missing the `notes.md` clause; R4 project-specific authored-deliverables prose; R5 reviewer
> invocation detail; R6/R7 supplementary text). To **guarantee byte-identical** shared workflow
> sections (the operator's "in sync" goal), replace extrends's two contiguous shared-workflow spans
> with CANON-1 wholesale, **preserving extrends's project-specific `## Project context` block** (which
> sits between them). This subsumes D1–D7 and R1–R7 in one stroke.

extrends's AGENTS.md order is: title → preamble → cross-agent → **`## Project context`** (project-
specific) → roles → openspec-workflow → change-tiers → state → working-process → web-research →
after-reading. So:
- **Span 1 — REPLACE** everything from the MANDATORY preamble blockquote through the end of
  `## Cross-agent compatibility` with **CANON-1's preamble + Cross-agent compatibility** (verbatim).
- **KEEP** extrends's `## Project context` section verbatim (TrendScope summary + hard-constraints:
  Python 3.12, SQLite/Postgres, free API tiers, cron execution model).
- **Span 2 — REPLACE** everything from `## Roles` through the end of `## After reading this file`
  with **CANON-1's Roles → After-reading** (verbatim).
- Result: extrends's shared workflow sections become byte-identical to CANON-1; only the title and the
  preserved Project-context block are extrends-specific. (Lost, harmlessly: extrends's R7
  "this replaces the old session-notes file" note and the R1/R2 idioms — none are load-bearing.)
- **F — add `ai-docs/fast-track-workflow.md`** = CANON-2 verbatim (dormant). (The AGENTS.md
  "Fast-track override" pointer arrives automatically via the Span-2 replace.)
- **decisions.md:** add an entry recording the tiers-standing + fast-track-autonomy-opt-in model
  (parity with the scaffold's new entry).
- **Orchestrator verification:** after apply, `diff` extrends's two spans against CANON-1 to confirm
  byte-identity, and confirm the Project-context block + the rest of the file (title) are intact.

> **Note on extrends git state:** extrends `main` is ahead of origin (~10 unpushed incl. the prior
> sync + the operator's own commits). These edits add more local commits; push only on go-ahead.

> **Note on extrends git state:** extrends `main` is ahead of origin (~10 unpushed incl. the prior
> sync + the operator's own commits). These edits add more local commits; push only on go-ahead.

---
---

# Appendix CANON-1 — canonical AGENTS.md workflow sections (verbatim)

> These sections are byte-identical across all three repos. Per-repo files wrap them with their own
> `# <project>` title, `## Project context` (+ hard-constraints), and (for psc-monitor) the technical
> reference body. Everything below from the MANDATORY blockquote through "After reading this file" is
> the shared canon.

```markdown
> **MANDATORY — read before doing anything else**
>
> You are reading this file. Before taking any action, also read **`STATUS.md`**,
> **`ai-docs/decisions.md`**, and **`ai-docs/open-questions.md`** in full. If you are
> *resuming an in-progress OpenSpec change*, also read that change's
> `openspec/changes/<name>/` directory (`proposal.md`, `design.md`, `tasks.md`,
> `notes.md`). Otherwise skip `openspec/changes/` and `ai-docs/archive/` — load a
> specific file there only when re-examining the closed decision it covers.
>
> These are the **starting source of truth**. They override your training data, general
> knowledge, and outside assumptions. If they conflict with the actual codebase,
> **update the files** to reflect reality — do not silently override or ignore the gap.
>
> On resume specifically, sanity-check freshness before trusting `STATUS.md`: run
> `git log --oneline -5` and confirm `STATUS.md` reflects those latest commits — if it
> lags, reconcile it to reality first.
>
> **Treat this file as stable.** Edit it only to add durable project context any future
> agent needs to orient — project purpose, constraints, process decisions. Current
> status, recent progress, and changeable decisions belong in `STATUS.md`,
> `openspec/changes/`, and `ai-docs/` respectively. Stability means this file caches
> well across sessions.
>
> If `STATUS.md` or `ai-docs/` do not exist, create them before doing anything else.

## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents** (OpenCode/DeepSeek/GLM).
For that to work, **all project state lives in tracked, agent-neutral files** — never in
harness-private storage. Concretely, do **not** read from, write to, or rely on:
- Global or cross-session memory, harness memory, or any assistant-specific config
  files/directories (`.claude/settings.local.json`, `CLAUDE.md`, memory files, etc.) —
  record project knowledge in `ai-docs/` and the OpenSpec artifacts instead.
- External repos or documentation you were not explicitly pointed to.

**Exception — shared workflow definitions, not private state.** The tracked
`.claude/skills/`, `.claude/agents/`, and `.opencode/agents/` directories ARE relied
upon by design: they are version-controlled and loaded by *both* harnesses (OpenCode
auto-discovers `.claude/skills/` — see `ai-docs/decisions.md`). The rule above bans
harness-*private* state/memory, not these shared, tracked definitions. (A tracked,
hook-free `.claude/settings.json` permissions file is also fine.)

Maintain this discipline for the **entire session**, not just at the start.

## Roles

- **The primary agent is the orchestrator and reviewer — not the implementer.** It runs
  the OpenSpec lifecycle (explore, propose, verify, archive) and reviews output; it does
  **not** write implementation code. Implementation happens in the **apply** phase, which
  is delegated (see below). Quick doc edits and commits are done by the primary directly
  — do not over-delegate trivia.
- **The apply-executor is a role, fillable by either agent family:** under Claude, the
  apply-executor is **deepseek-v4-flash driven via `opencode run`**, with a **Sonnet
  subagent as fallback** (see the apply/verify skills for the exact failure ladder); under
  OpenCode, it is **DeepSeek V4 Flash** (`@apply-executor`). Either way it implements
  `tasks.md` **sequentially**, top to bottom, checking off each task as it lands.
- **The archive-executor is a role for the archive phase:** under Claude it is **deepseek-v4-pro
  driven via `opencode run`**, with a **Sonnet subagent as fallback**; under OpenCode it is
  **DeepSeek V4 Pro** (`@archive-executor`). It moves the change dir, syncs delta specs, and
  reconciles `STATUS.md` / `ai-docs/decisions.md` / `ai-docs/open-questions.md` into a durable
  handoff. Reconciliation is judgment-heavy, so it runs on the **pro** tier — unlike the
  mechanical apply-executor (flash).
- **The `@openspec-reviewer` (deepseek-v4-pro)** is a read-only auditor invoked automatically
  during **propose** to review artifacts *before* implementation. It surfaces defects;
  it never edits. Under Claude Code it is invoked via
  `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`
  (`.opencode/agents/openspec-reviewer.md`); under OpenCode via the Task tool with
  `subagent_type: "openspec-reviewer"`.

## OpenSpec workflow

All non-trivial feature work follows the OpenSpec lifecycle:

1. **explore** — research and scope; writes `explore-brief.md`.
2. **propose** — generate proposal, design, tasks; `@openspec-reviewer` audits each
   before freeze.
3. **apply** — delegate implementation to the apply-executor.
4. **verify** — deep behavioral review by the orchestrator.
5. **archive** — close the change; promote specs; reconcile project docs.

**Phase-specific procedural rules live in the skill files, not here.**
The agent invokes the appropriate skill (via its harness's skill mechanism) when a phase is
entered. AGENTS.md carries only cross-cutting rules that span multiple phases.
Skill files: `.claude/skills/openspec-*/SKILL.md` (discovered by both harnesses — see
`ai-docs/decisions.md`).

> **Fast-track override:** A fast-track workflow exists in `ai-docs/fast-track-workflow.md`
> for high-capability agents the operator explicitly trusts — it lets you proceed
> **autonomously**, working the normal interactive checkpoints without pausing for
> confirmation. **Do NOT use it unless the operator has explicitly granted you fast-track
> authority** for this session or task — otherwise follow the normal, phase-gated workflow
> here and in the skills. (Tiering, below, is standing and applies regardless.)

OpenSpec artifacts live in `openspec/changes/<name>/`.

## Change tiers

Scale process weight to risk; classify every change yourself and **state the tier** (the operator
initiates tier-2/tier-3 lifecycles):

- **SMALL** — skip the full OpenSpec lifecycle, but still: (1) write a plan checkpointed to a standard
  dir (the change dir or `plans/`), (2) delegate execution to **deepseek-v4-flash** via
  `opencode run --agent apply-executor`, (3) do your own verification.
- **MEDIUM** — run the OpenSpec lifecycle, except **propose** emits only `tasks.md`, reviewed by
  **deepseek-v4-pro** before freeze; change-specific acceptance criteria go in the change's `notes.md`.
- **COMPLEX / UNCERTAIN** — full OpenSpec process (proposal + design + tasks, reviewed).

You never write implementation code beyond a single disclosed one-line exception. **Pushes to `main`
require explicit operator authorization.** Exact opencode invocations and the crash→retry→Sonnet
failure ladder live in `.claude/skills/openspec-apply-change/SKILL.md`.

## State, write discipline, and the archive-as-handoff rule

Two tiers of state, with deliberately different write rules:

- **Change-local scratch — write continuously, in-context.** During a change, freely
  write its `openspec/changes/<name>/` files: check off `tasks.md` as tasks land, append
  decisions / rejected approaches / discoveries to `notes.md`, log reviews in
  `review-log.md`. These writes are cheap because they happen while the relevant context
  is already loaded. The change dir is the scratch log.
- **Project-tracked docs — write-deferred, reconciled at archive by a delegated executor.**
  Do **not** incrementally edit `STATUS.md`, `ai-docs/decisions.md`, or
  `ai-docs/open-questions.md` during busy work in a bloated context. They are reconciled
  **once**, during **archive**, by a delegated `deepseek/deepseek-v4-pro`
  archive-executor (under Claude: via `opencode run`; under OpenCode: a subagent), then
  reviewed and committed by the primary. The executor runs with fresh context seeded from
  the compact, structured change dir artifacts — not the conversation transcript. This
  keeps the expensive multi-file reconciliation cheap: low context in, structured source
  read. **This is the single load-bearing rule that preserves token economy — do not move
  the reconciliation back into the working session.**

## Working process

- **Default to scripts over LLM token-burn for deterministic work — everywhere.** When a
  task is mechanical and reproducible (data scans, extraction, bulk transforms, repetitive
  checks), write a small script and run it. Prefer the `scripts/_*_oneoff.py` convention;
  dump non-trivial output to disk as JSON/CSV — that artifact becomes the durable,
  re-runnable input the reasoning consumes. Spend tokens on *judgment*, not on
  re-deriving by hand what a script reproduces for free.
- **Make work resumable.** This harness has **no subagent resume**; a killed agent
  restarts cold. Push deterministic heavy-lifting into re-runnable scripts that dump
  intermediate results to disk; checkpoint partial findings as each section completes;
  decompose long jobs into steps that each complete and return. Granularity buys
  resumability. Long-running batches must be resumable from a checkpoint and **stop on
  first failure** rather than continuing with partial state.
- **Use subagents for independent work.** Parallelize independent research/extraction
  across subagents freely; prefer a cheaper model (e.g. Sonnet) for extraction. Always
  apply your own judgment to their reports — they have been wrong before — and have each
  subagent checkpoint findings to disk so the work survives interruption. **Do not fan out
  cohesive, dependency-laden work** (e.g. the apply phase's sequential tasks): concurrent
  writers on one working tree corrupt each other — which is exactly why apply uses a single
  sequential executor. Delegation saves time/cost only when the subtasks are genuinely
  independent.
- **Tests green before any commit.** The apply-executor does **not** commit; the
  orchestrator reviews and commits in small, reviewed checkpoints (one logical change
  each). Prefer invariant/property tests over output-pinning tests. **Never record test,
  doc, or row counts in any tracked doc** (`STATUS.md`, `ai-docs/`, change `notes.md`) —
  not as a live-status figure and **not as a historical record**. "Tests pass" and
  "the system ran clean" are the only signals that matter; the sole exception is a
  *failing or newly-skipped* test, recorded as a note with its cause — never a passing
  tally.
- **Commit to `main` by default; push only with authorization.** Unless a project
  specifies otherwise, committing to `main` is fine without asking (in the small, tested
  checkpoints described above) — but **push to the remote only with explicit operator
  authorization**. Where a project uses a PR/merge flow, standing merge authorization is
  scoped to a named queue and to PRs whose own CI run passed — report each merge.
- **Design lives in two places by horizon:** *per-change* design → the change's
  `design.md`. *Multi-change / long-horizon roadmap* that doesn't map to a single change
  → `plans/`. Prune `plans/` as roadmap items become real changes.
- **Authored deliverables go only to the standard agent-neutral dirs** — `plans/` (roadmap/
  design direction), `ai-docs/decisions.md` (ratified decisions), `ai-docs/open-questions.md`
  (open follow-ons), `ai-docs/archive/` (historical/process records), `openspec/changes/<name>/`
  (change artifacts). **Never** write deliverables into a harness-specific directory.
- **Guard destructive and external operations.** Never add a destructive operation
  (SQL `TRUNCATE`/`DROP`/`DELETE`-without-filter, and the like) without an
  input-confirmation guard. When running tests, blank or override external-service
  credentials (email/SMS/payment) so the suite can't send real messages or incur charges.
- **Mind data scale.** For data too large to fit in memory, stream or use SQL
  set-operations — never load the full dataset into process memory. Before the first
  at-scale run of changed data code, audit each step's input domain (bounded by this run,
  or by all history?) and check for unbounded in-memory loads (e.g. `fetchall()` on an
  unbounded query) — a green suite at fixture scale says nothing about production volume.
- **One canonical file per category.** Keep exactly one source for each kind of thing
  (dependency manifest, open-issues list, schema, etc.); when a duplicate drifts, delete
  it rather than maintaining both. When a tracked item completes or becomes moot, close
  it explicitly in its tracker rather than leaving a stale entry.
- Plan non-trivial work before executing; ask the user when genuinely unsure rather than
  guessing.

## Web research convention

**(a) GitHub files — always fetch raw, never clone.** Fetch via
`raw.githubusercontent.com` or run `python scripts/fetch_clean.py <github-url>`. Do NOT
`git clone` whole repos.
**(b) Full-page content — use `fetch_clean`** (`python scripts/fetch_clean.py <url>`).
Use built-in WebFetch only for a targeted single-fact answer.
**(c) Be targeted** — only fetch what you will cite; checkpoint findings to disk.
**(d) Never call the built-in `WebSearch` tool from the main thread.** Route ALL web research
through subagents that use `scripts/fetch_clean.py` (discover via a fetched search URL, then
fetch the chosen pages). This keeps the orchestrator context clean and lets research run in
parallel and checkpoint to disk; the orchestrator applies its own judgment to subagent reports.

## After reading this file
Acknowledge four things before acting: (1) your role as orchestrator/reviewer who runs
the OpenSpec lifecycle and does not implement; (2) that apply is delegated to a
sequential apply-executor and verify is *your* deep behavioral review; (3) that when
verify finds a bug you diagnose and scope it, then re-delegate the fix to a fresh
executor (deepseek-first, Sonnet-fallback — see verify skill for the ladder; only
trivial typo-level changes inline); (4) that you write the change dir
continuously but reconcile `STATUS.md`/`ai-docs/` only at archive, by delegating
to the archive-executor (deepseek-v4-pro), then reviewing and committing.
```

---
---

# Appendix CANON-2 — canonical `ai-docs/fast-track-workflow.md` (verbatim, autonomy-only, dormant)

> Byte-identical across all three repos. Slimmed from the scaffold's current file: the tier
> definitions are removed (tiers are standing in AGENTS.md `## Change tiers`); this file governs only
> the **autonomy override**. No active grant note in any repo (Option A).

```markdown
# Fast-Track Workflow (trusted agents only)

> **STOP AND READ THIS GATE BEFORE PROCEEDING.**
>
> This is an **opt-in override** for high-capability agents that the operator — the human directing this work — explicitly trusts to iterate with minimal human checkpoints. It exists because such agents need fewer checks and balances to produce correct output.
>
> **The default for every agent is the normal, phase-gated OpenSpec workflow** (AGENTS.md + the openspec-* skills). This file does not replace that default — it overrides only the *interactive checkpointing*, and only when the operator says so.
>
> You may use the autonomy shortcut in this file **only if the operator has explicitly granted you fast-track authority** for this session or task.
>
> **If you are reading this without that explicit grant: stop, ignore this file, and use the normal workflow.**
>
> This file governs **autonomy only**. Change **tiering** (SMALL / MEDIUM / COMPLEX) is *standing* and lives in AGENTS.md `## Change tiers` — it applies whether or not fast-track is granted.

---

## Operating under fast-track

Once granted, you proceed **autonomously** — work through the workflow's normal interactive checkpoints without pausing to ask the operator for confirmation, using your own judgment at each step. The entire point is full execution without per-step prompting. Collect uncertainties into an end-of-work report rather than interrupting mid-flight.

**Still stop and ask the operator when:**
- A requirement is genuinely ambiguous and you cannot make a safe default call.
- An action is irreversible or destructive (data loss, force-push, deleting non-restorable work), spends money, or is an operator-only ("Track A") action.

**Always disclose** what you did: the tier you assigned each change, any delegations made, and any fallbacks taken.

---

## Guardrails that never relax

These apply regardless of fast-track or tier.

- **You are the orchestrator/reviewer, not the implementer.** No hand-written implementation code beyond a single trivial one-liner — and that exception must be disclosed every time. Execution is always delegated to the apply-executor.
- **Delegation mechanics are identical to the normal workflow:**
  - Use the same `opencode run` executor/reviewer invocations.
  - Assert that the real agent actually ran (do not accept a self-report).
  - Judge success from disk via `git diff` and task check-offs — not the agent's own claim of success.
  - Failure ladder: operational crash → retry once → Sonnet subagent; non-crash failure → Sonnet immediately. Always disclose any fallback taken.
- **Verify is always real.** Even a SMALL change requires a diff read and a behavioral test. Never mark a change done off a green test suite alone.
- **Archive runs normally.** For MEDIUM and COMPLEX, archive per the normal archive skill — do not skip it.
- **Executors never commit.** You review the diff, then you commit. Pushes to `main` still require explicit operator authorization.
```
