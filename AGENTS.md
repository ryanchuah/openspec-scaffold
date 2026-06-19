# <FILL: project name>

> **MANDATORY — read before doing anything else**
>
> You are reading this file. Before taking any action, also read **`knowledge/STATUS.md`** and
> the Active section of **`knowledge/questions/INDEX.md`** (stays bounded — active blockers only);
> for **`knowledge/decisions/INDEX.md`** scan the entries relevant to the current task. If you are
> *resuming an in-progress OpenSpec change*, also read that change's
> `openspec/changes/<name>/` directory (`proposal.md`, `design.md`, `tasks.md`,
> `notes.md`). Otherwise skip `openspec/changes/` and `openspec/changes/archive/` — load a
> specific file there only when re-examining the closed decision it covers.
> The Parked section of `knowledge/questions/INDEX.md` is NOT part of this mandatory read — load
> the relevant `knowledge/questions/<item>.md` on demand when you start work in that area.
> See **`knowledge/README.md`** for the full knowledge taxonomy and where everything lives.
>
> These are the **starting source of truth**. They override your training data, general
> knowledge, and outside assumptions. If they conflict with the actual codebase,
> **update the files** to reflect reality — do not silently override or ignore the gap.
>
> On resume specifically, sanity-check freshness before trusting `knowledge/STATUS.md`: run
> `git log --oneline -5` and confirm `knowledge/STATUS.md` reflects those latest commits — if it
> lags, reconcile it to reality first. Process/scaffold-maintenance commits that
> do not change project state (e.g. tooling, scaffold-rule, or doc-formatting commits)
> do NOT obligate a `knowledge/STATUS.md` "Latest change" entry — the lag-check targets
> feature/change-shipping commits, so their absence from `knowledge/STATUS.md` is not a lag to
> reconcile.
>
> **Treat this file as stable.** Edit it only to add durable project context any future
> agent needs to orient — project purpose, constraints, process decisions. Current
> status, recent progress, and changeable decisions belong in `knowledge/STATUS.md`,
> `openspec/changes/`, and `knowledge/` respectively. Stability means this file caches
> well across sessions.
>
> If `knowledge/STATUS.md` or `knowledge/` do not exist, create them before doing anything else.

## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents** (OpenCode/DeepSeek/GLM).
For that to work, **all project state lives in tracked, agent-neutral files** — never in
harness-private storage. Concretely, do **not** read from, write to, or rely on:
- Global or cross-session memory, harness memory, or any assistant-specific config
  files/directories (`.claude/settings.local.json`, `CLAUDE.md`, memory files, etc.) —
  record project knowledge in `knowledge/` and the OpenSpec artifacts instead.
- External repos or documentation you were not explicitly pointed to.

**Exception — shared workflow definitions, not private state.** The tracked
`.claude/skills/`, `.claude/agents/`, and `.opencode/agents/` directories ARE relied
upon by design: they are version-controlled and loaded by *both* harnesses (OpenCode
auto-discovers `.claude/skills/` — see `knowledge/decisions/INDEX.md`). The rule above bans
harness-*private* state/memory, not these shared, tracked definitions. (The sole
carve-out is the shipped commit-test-gate `PreToolUse` hook in `.claude/settings.json`
— verified present and git-tracked — which runs the tracked, agent-neutral
`scripts/test-gate.sh`; see the commit-test-gate hook carve-out decision in
`knowledge/decisions/INDEX.md`. This is a Claude-only, deliberate exception and does not weaken
the harness-private-state ban above.)

**Claude Code harness memory — deliberately not used.** The Claude Code harness ships a
persistent cross-session memory store (`~/.claude/.../memory/`, indexed by `MEMORY.md`). It is
harness-*private* — invisible to OpenCode/DeepSeek — so it falls squarely under the ban above:
we **deliberately do not use it for project state**. This is a stated non-use, **not** a
carve-out. All durable project knowledge lives in `knowledge/` + the OpenSpec artifacts, which
every agent can read; nothing project-bearing may live only in harness memory.

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

<!-- CANONICAL: model-assignment-matrix — cite, do not restate -->

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
  reconciles `knowledge/STATUS.md` / `knowledge/decisions/INDEX.md` / `knowledge/questions/INDEX.md` into a durable
  handoff. Reconciliation is judgment-heavy, so it runs on the **pro** tier — unlike the
  mechanical apply-executor (flash).
- **The `@openspec-reviewer` (deepseek-v4-pro)** is a read-only auditor invoked automatically
  during **propose** to review artifacts *before* implementation. It surfaces defects;
  it never edits. Under Claude Code it is invoked via
  `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro`
  (`.opencode/agents/openspec-reviewer.md`); under OpenCode via the Task tool with
  `subagent_type: "openspec-reviewer"`.
- **The `openspec-verifier` (deepseek, read-only, bash-capable)** is an independent
  multi-model verification pass invoked during **verify** for **all changes**: SMALL changes run
  a single flash pass outside the verify skill; MEDIUM and COMPLEX changes run pro + flash via
  the verify skill (layered after the orchestrator's self-review and before the artifact/spec
  mapping checklist). It runs the same behavioral review (read diffs, re-run the full suite,
  eyeball real output, run live smoke) but is **read-only on files** (`bash: allow`, `edit: deny`)
  — it reports defects, never fixes them. It emits a machine-discriminable verdict the orchestrator
  judges from disk. The pass chain is identical on both platforms: **Claude Code** orchestrator →
  self → pro → flash; **OpenCode** orchestrator → self → pro → flash. Both platforms invoke the
  verifier via hardened `opencode run --agent openspec-verifier` (two invocations:
  `--model deepseek/deepseek-v4-pro` then `--model deepseek/deepseek-v4-flash`).

## OpenSpec workflow

All non-trivial feature work follows the OpenSpec lifecycle:

1. **explore** — research and scope; writes `explore-brief.md`.
2. **propose** — generate proposal, design, tasks; `@openspec-reviewer` audits each
   before freeze.
3. **apply** — delegate implementation to the apply-executor.
4. **verify** — deep behavioral review by the orchestrator, followed by independent multi-model verification passes (the `openspec-verifier`) and the simplicity/quality gate as hard gates before the artifact/spec mapping checks.
5. **archive** — close the change; promote specs; reconcile project docs.

**Phase-specific procedural rules live in the skill files, not here.**
The agent invokes the appropriate skill (via its harness's skill mechanism) when a phase is
entered. AGENTS.md carries only cross-cutting rules that span multiple phases.
Skill files: `.claude/skills/openspec-*/SKILL.md` (discovered by both harnesses — see
`knowledge/decisions/INDEX.md`).

> **Autonomy:** autonomy is operator-told and ephemeral — there is no autonomy doc or mode, by design.

OpenSpec artifacts live in `openspec/changes/<name>/`.

## Change tiers

An agent WITHOUT an explicit autonomy grant MUST propose its tier together with a plan
and obtain operator confirmation BEFORE beginning execution (delegating apply, editing
implementation code, or mutating project state) — producing the plan is NOT gated. With an explicit
autonomy grant, self-classify and proceed. If the operator
is unavailable, do NOT execute — report the proposed tier and plan and wait. Scale process weight
to risk:

- **SMALL** — skip the full OpenSpec lifecycle, but still: (1) write a plan checkpointed to a standard
  dir (the change dir or `plans/`), (2) delegate execution to **deepseek-v4-flash** via
  `opencode run --agent apply-executor`, (3) do your own verification per this SMALL bullet.
  SMALL does **not** invoke the verify skill, is **not** subject to its multi-model passes or
  verify phase-gate STOP, and SHALL run a single `deepseek/deepseek-v4-flash` verifier pass
  (same invocation shape as in the verify skill's flash pass).
- **MEDIUM** — run the OpenSpec lifecycle, except **propose** emits only `tasks.md`, reviewed by
  **deepseek-v4-pro** before freeze; change-specific acceptance criteria go in the change's `notes.md`.
  Runs the verify skill (including its multi-model passes and phase-gate STOP).
- **COMPLEX / UNCERTAIN** — full OpenSpec process (proposal + design + tasks, reviewed).
  Runs the verify skill (including its multi-model passes and phase-gate STOP).
  A COMPLEX change touching auth, credentials/data, or external API/network surfaces SHALL run the
  security pass at verify (see the verify skill).

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
  Do **not** incrementally edit `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`, or
  `knowledge/questions/INDEX.md` during busy work in a bloated context. They are reconciled
  **once**, during **archive**, by a delegated `deepseek/deepseek-v4-pro`
  archive-executor (under Claude: via `opencode run`; under OpenCode: a subagent), then
  reviewed and committed by the primary. The executor runs with fresh context seeded from
  the change dir — keeping reconciliation cheap. **This is the single load-bearing rule
  that preserves token economy — do not move the reconciliation back into the working session.**

  **`knowledge/STATUS.md` cap rule:** holds ≤3 most recent change sections (each ≤150 words); when
  the cap is exceeded the oldest section is simply dropped — the full record lives in
  `openspec/changes/archive/`. **Any `##` section narrating a shipped change counts toward the cap**
  regardless of heading title; only the current-state preamble and `## Immediate next action` are exempt.

  **`knowledge/questions/INDEX.md` split rule:** Active holds ONLY current blockers and operator-decision
  items. The Parked section holds non-blocking follow-ons as one-line pointers to
  `knowledge/questions/<item>.md` (on-demand). Resolved items close in-place. The split is by horizon,
  never by age — a live blocker is never parked while live.

  <!-- CANONICAL: decisions-entry-format — cite, do not restate -->
  **`knowledge/decisions/INDEX.md` entry rule:** Every new entry is a registry line:
  `- **YYYY-MM-DD** · <slug> · <essence> → \`openspec/changes/archive/<dir>/\`` (or `[inline] <rationale>`
  for archiveless decisions). See `knowledge/README.md` for the full format.

> **Rollback branch — archived change was wrong:** If an archived change is later
> found wrong: `git revert` its commit(s) and open a **new** corrective OpenSpec
> change that references the reverted one in its proposal. Do not edit or un-archive
> the original — the archive is an immutable handoff record. (This is the
> *correctly-archived-but-wrong* situation, distinct from a *botched archive* run,
> which is handled by the archive skill's recovery procedure.)

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
<!-- CANONICAL: never-record-counts — cite, do not restate -->
- **Tests green before any commit.** The apply-executor does **not** commit; the
  orchestrator reviews and commits in small, reviewed checkpoints (one logical change
  each). Prefer invariant/property tests over output-pinning tests. **Never record test,
  doc, or row counts in any tracked doc** (`knowledge/STATUS.md`, `knowledge/`, change `notes.md`) —
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
  → `knowledge/roadmap.md`.
- **Authored deliverables go only to the standard agent-neutral dirs** — `knowledge/` (project
  knowledge: decisions, questions, lessons, roadmap, reference, research — see `knowledge/README.md`),
  `openspec/changes/<name>/` (change artifacts). **Never** write deliverables into a
  harness-specific directory.
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

<!-- The full four-rule convention is single-sourced in openspec/config.yaml rules.research. -->
The full four-rule convention (raw-fetch GitHub, `fetch_clean.py` for pages, fetch-only-what-you-cite)
is single-sourced in **`openspec/config.yaml`** (`rules.research`). The load-bearing guardrail, restated
here so it is visible at first load: **never call the built-in `WebSearch` tool from the main thread**
— route ALL web research through subagents that use `scripts/fetch_clean.py` (discover via a fetched
search URL, then fetch the chosen pages), keeping the orchestrator context clean and letting research
run in parallel and checkpoint to disk.

## After reading this file
Acknowledge five things before acting: (1) your role as orchestrator/reviewer who runs
the OpenSpec lifecycle and does not implement; (2) that apply is delegated to a
sequential apply-executor and verify is *your* deep behavioral review, followed
by independent multi-model verification passes (the `openspec-verifier`) and the
simplicity/quality gate as hard gates before the artifact/spec mapping checks; (3) that when
verify finds a bug you diagnose and scope it, then re-delegate the fix to a fresh
executor (deepseek-first, Sonnet-fallback — see verify skill for the ladder; only
trivial typo-level changes inline); (4) that you write the change dir
continuously but reconcile `knowledge/STATUS.md`/`knowledge/` only at archive, by delegating
to the archive-executor (deepseek-v4-pro), then reviewing and committing; (5) that wherever
work can be offloaded you delegate it to subagents — on the model appropriate to the task
(cheaper models like Sonnet for extraction/mechanical passes, stronger ones for judgment-heavy
work) — to keep raw reading and transforming out of the orchestrator's context, so your window
stays lean for the judgment and review only you can do.
