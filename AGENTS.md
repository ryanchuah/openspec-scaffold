# <FILL: project name>

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
harness-*private* state/memory, not these shared, tracked definitions. (The sole
carve-out is the shipped commit-test-gate `PreToolUse` hook in `.claude/settings.json`
— verified present and git-tracked — which runs the tracked, agent-neutral
`scripts/test-gate.sh`; see the commit-test-gate hook carve-out decision in
`ai-docs/decisions.md`. This is a Claude-only, deliberate exception and does not weaken
the harness-private-state ban above.)

Maintain this discipline for the **entire session**, not just at the start.

## Project context

Authoritative one-paragraph summary, tech stack, and testing philosophy live in
**`openspec/config.yaml`** (`context:`), because that block is injected into every
OpenSpec artifact prompt — keep it as the single short source and do not duplicate it
at length here.

<FILL: 2-4 sentences of detailed, load-bearing context too long for the config.yaml
prompt-injection block — scope rules, what the product must/must never do, etc. Remove
this section if the config.yaml context is sufficient.>

**Hard constraints:** <FILL: API tiers, cost limits, platform/runtime constraints,
anything the agent must never violate — or remove this section if none.>

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
- **The `openspec-verifier` (deepseek, read-only, bash-capable)** is an independent
  multi-model verification pass invoked during **verify**, layered after the orchestrator's
  self-review and before the artifact/spec mapping checklist. It runs the same behavioral
  review (read diffs, re-run the full suite, eyeball real output, run live smoke) but is
  **read-only on files** (`bash: allow`, `edit: deny`) — it reports defects, never fixes
  them. It emits a machine-discriminable verdict the orchestrator judges from disk. The
  platform-dependent pass chain is: **Claude Code** orchestrator → self → pro → flash;
  **OpenCode** orchestrator → self → flash only (an OpenCode orchestrator already runs
  deepseek-v4-pro, so only the cheaper flash tier adds independent model diversity).
  Under Claude Code the verifier is invoked via hardened `opencode run --agent openspec-verifier`
  (two invocations: `--model deepseek/deepseek-v4-pro` then `--model deepseek/deepseek-v4-flash`);
  under OpenCode via the Task tool with `subagent_type: openspec-verifier` (runs the frontmatter
  default flash, no override).

## OpenSpec workflow

All non-trivial feature work follows the OpenSpec lifecycle:

1. **explore** — research and scope; writes `explore-brief.md`.
2. **propose** — generate proposal, design, tasks; `@openspec-reviewer` audits each
   before freeze.
3. **apply** — delegate implementation to the apply-executor.
4. **verify** — deep behavioral review by the orchestrator, followed by independent multi-model verification passes (the `openspec-verifier`) as hard gates before the artifact/spec mapping checks.
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

An agent WITHOUT an explicit fast-track/autonomy grant MUST propose its tier together with a plan
and obtain operator confirmation BEFORE beginning execution (delegating apply, editing
implementation code, or mutating project state) — producing the plan is NOT gated. With an explicit
fast-track grant, self-classify and proceed per `ai-docs/fast-track-workflow.md`. If the operator
is unavailable, do NOT execute — report the proposed tier and plan and wait. Scale process weight
to risk:

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
sequential apply-executor and verify is *your* deep behavioral review, followed
by independent multi-model verification passes (the `openspec-verifier`) as hard
gates before the artifact/spec mapping checks; (3) that when
verify finds a bug you diagnose and scope it, then re-delegate the fix to a fresh
executor (deepseek-first, Sonnet-fallback — see verify skill for the ladder; only
trivial typo-level changes inline); (4) that you write the change dir
continuously but reconcile `STATUS.md`/`ai-docs/` only at archive, by delegating
to the archive-executor (deepseek-v4-pro), then reviewing and committing.
