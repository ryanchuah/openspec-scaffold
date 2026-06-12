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
> **Treat this file as stable.** Edit it only to add durable project context any future
> agent needs to orient — project purpose, constraints, process decisions. Current
> status, recent progress, and changeable decisions belong in `STATUS.md`,
> `openspec/changes/`, and `ai-docs/` respectively. Stability means this file caches
> well across sessions.
>
> If `STATUS.md` or `ai-docs/` do not exist, create them before doing anything else.

## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents** (OpenCode/DeepSeek).
For that to work, **all project state lives in tracked, agent-neutral files** — never in
harness-private storage. Concretely, do **not** read from, write to, or rely on:
- Global or cross-session memory, harness memory, or any assistant-specific config
  files/directories (`.claude/`, `CLAUDE.md`, memory files, etc.) — record project
  knowledge in `ai-docs/` and the OpenSpec artifacts instead.
- External repos or documentation you were not explicitly pointed to.

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
  subagent as fallback** (see the apply skill for the exact failure ladder); under
  OpenCode, it is **DeepSeek V4 Flash** (`@apply-executor`). Either way it implements
  `tasks.md` **sequentially**, top to bottom, checking off each task as it lands.
- **The `@openspec-reviewer` (`deepseek/deepseek-v4-pro`)** is a read-only auditor
  invoked automatically during **propose** to review artifacts *before* implementation.
  It surfaces defects; it never edits. Under Claude Code, it is invoked via
  `opencode run --agent openspec-reviewer --model deepseek/deepseek-v4-pro` (the agent
  definition lives at `.opencode/agents/openspec-reviewer.md`). Under OpenCode, it is
  called via the Task tool with `subagent_type: "openspec-reviewer"`.

## OpenSpec workflow

All non-trivial feature work follows the OpenSpec lifecycle:

1. **explore** — research and scope; writes `explore-brief.md`.
2. **propose** — generate proposal, design, tasks; `@openspec-reviewer` audits each
   before freeze.
3. **apply** — delegate implementation to the apply-executor.
4. **verify** — deep behavioral review by the orchestrator.
5. **archive** — close the change; promote specs; reconcile project docs.

**Phase-specific procedural rules live in the skill files, not here.**
The agent invokes the appropriate skill (via the Skill tool) when a phase is entered.
AGENTS.md carries only cross-cutting rules that span multiple phases.
Skill files: `.claude/skills/openspec-*-change/SKILL.md`.

OpenSpec artifacts live in `openspec/changes/<name>/`.

## State, write discipline, and the archive-as-handoff rule

Two tiers of state, with deliberately different write rules:

- **Change-local scratch — write continuously, in-context.** During a change, freely
  write its `openspec/changes/<name>/` files: check off `tasks.md` as tasks land, append
  decisions / rejected approaches / discoveries to `notes.md`, log reviews in
  `review-log.md`. These writes are cheap because they happen while the relevant context
  is already loaded. The change dir is the scratch log.
- **Project-tracked docs — write-deferred, reconciled at archive in a FRESH session.**
  Do **not** incrementally edit `STATUS.md`, `ai-docs/decisions.md`, or
  `ai-docs/open-questions.md` during busy work in a bloated context. They are reconciled
  **once**, during **archive**, and the preferred path is to run archive **in a
  fresh session seeded from the change dir** (the compact, structured artifacts — not the
  conversation transcript). This keeps the expensive multi-file reconciliation cheap: low
  context in, structured source read. **This is the single load-bearing rule that
  preserves token economy — do not move the reconciliation back into the working
  session.**

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
  resumability.
- **Tests green before any commit.** The apply-executor does **not** commit; the
  orchestrator reviews and commits in small, reviewed checkpoints (one logical change
  each). Prefer invariant/property tests over output-pinning tests. **Never record test,
  doc, or row counts in any tracked doc** (`STATUS.md`, `ai-docs/`, change `notes.md`) —
  not as a live-status figure and **not as a historical record**. "Tests pass" and
  "the system ran clean" are the only signals that matter; the sole exception is a
  *failing or newly-skipped* test, recorded as a note with its cause — never a passing
  tally.
- **Design lives in two places by horizon:** *per-change* design → the change's
  `design.md`. *Multi-change / long-horizon roadmap* that doesn't map to a single change
  → `plans/`. Prune `plans/` as roadmap items become real changes.
- Plan non-trivial work before executing; ask the user when genuinely unsure rather than
  guessing.

## Web research convention

**(a) GitHub files — always fetch raw, never clone.** Fetch via
`raw.githubusercontent.com` or run `python scripts/fetch_clean.py <github-url>`. Do NOT
`git clone` whole repos.
**(b) Full-page content — use `fetch_clean`** (`python scripts/fetch_clean.py <url>`).
Use built-in WebFetch only for a targeted single-fact answer.
**(c) Be targeted** — only fetch what you will cite; checkpoint findings to disk.

## After reading this file
Acknowledge four things before acting: (1) your role as orchestrator/reviewer who runs
the OpenSpec lifecycle and does not implement; (2) that apply is delegated to a
sequential apply-executor and verify is *your* deep behavioral review; (3) that when
verify finds a bug you diagnose and scope it, then re-delegate the fix to a fresh
executor (deepseek-first, Sonnet-fallback — see verify skill for the ladder; only
trivial typo-level changes inline); (4) that you write the change dir
continuously but reconcile `STATUS.md`/`ai-docs/` only at archive, preferably in
a fresh session.
