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

This repo may be worked by **multiple agent families** (e.g. OpenCode/DeepSeek/GLM and
Claude). For that to work, **all project state lives in tracked, agent-neutral files** —
never in harness-private storage. Concretely, do **not** read from, write to, or rely on:
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
- **The apply-executor is a role, fillable by either agent family:** a **subagent** of
  the primary's family when the primary is Claude (a Sonnet subagent), or
  **`@apply-executor`** (DeepSeek V4 Flash) under OpenCode. Either way it implements
  `tasks.md` **sequentially**, top to bottom, checking off each task as it lands.
- **The `@openspec-reviewer` (GLM 5.1)** is a read-only auditor invoked automatically
  during **propose** to review artifacts *before* implementation. It surfaces defects;
  it never edits. *(OpenCode path only — GLM is not available under Claude Code; on the
  Claude path the **primary self-reviews** each artifact against the success criteria
  before freezing it.)*

## OpenSpec workflow

All non-trivial feature work follows the OpenSpec lifecycle:

1. **explore** (`/opsx:explore`) — research and scope; writes `explore-brief.md`.
2. **propose** (`/opsx:propose <name>`) — generate `proposal.md`, `design.md`,
   `tasks.md`; `@openspec-reviewer` audits each before it is frozen (`review-log.md`).
3. **apply** (`/opsx:apply`) — **do not implement in the primary session.** Pass the
   paths to `proposal.md`, `design.md`, `tasks.md` to the apply-executor. It works
   `tasks.md` sequentially and checks off tasks. Review its completion report before
   verify.
4. **verify** (`/opsx:verify`) — **this is the orchestrator's deep behavioral review,
   not a rubber stamp.** Read the actual diffs (do not trust the executor's summary);
   re-run the **full test suite yourself** (a green exit is necessary but not sufficient);
   **eyeball the real output** the code produces by running the system on real input and
   inspecting the actual result it generates — the records/rows selected, the text
   produced, the request sent — not just that tests pass. Prefer a re-runnable probe
   script in `scripts/` so the check is cheap to repeat. **When verify finds a defect,
   diagnose and scope the fix, then re-delegate it to a fresh apply-executor with a
   self-contained fix-spec — never hand-fix it yourself.** Inline exception is narrow: a
   typo, comment, or one-line rename. If you would write more than ~2 lines of
   implementation, stop and re-delegate.
5. **archive** (`/opsx:archive`) — close the change; promote specs into
   `openspec/specs/`. **This is also the project-state reconciliation (handoff) step —
   see below.**

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
  **once**, during **`/opsx:archive`**, and the preferred path is to run archive **in a
  fresh session seeded from the change dir** (the compact, structured artifacts — not the
  conversation transcript). This keeps the expensive multi-file reconciliation cheap: low
  context in, structured source read. **This is the single load-bearing rule that
  preserves token economy — do not move the reconciliation back into the working
  session.**

At archive, reconcile:
- `STATUS.md` — `Immediate next action` names the very next concrete step. `§ Done` is a
  permanent **pointer to `openspec/changes/archive/`** and never grows by hand.
- `ai-docs/decisions.md` — record every decision unlikely to change, **with a Why**.
  Never fabricate a rationale: if the motivation is unclear and matters, ask the user; if
  it doesn't matter enough to ask, omit it. Mark superseded decisions, don't delete.
- `ai-docs/open-questions.md` — open questions and **user-action items** (credentials,
  API keys, toggles), flagged BLOCKING where they gate other work.
- **Negative results preserved** — approaches investigated and rejected, **with the
  reason**, so they aren't re-attempted.

## Working process

- **Default to scripts over LLM token-burn for deterministic work — everywhere.** When a
  task is mechanical and reproducible (data scans, extraction, bulk transforms, repetitive
  checks), write a small script in `scripts/` and run it; dump non-trivial output to disk
  as JSON/CSV — that artifact becomes the durable, re-runnable input the reasoning
  consumes. Spend tokens on *judgment*, not on re-deriving by hand what a script
  reproduces for free.
- **Make work resumable.** Subagents may not be resumable and session limits are
  unpredictable, so a killed agent restarts cold. Push deterministic heavy-lifting into
  re-runnable scripts that dump intermediate results to disk; checkpoint partial findings
  as each section completes; decompose long jobs into steps that each complete and return.
  Granularity buys resumability.
- **Tests green before any commit.** The apply-executor does **not** commit; the
  orchestrator reviews and commits in small, reviewed checkpoints (one logical change
  each). Prefer invariant/property tests over output-pinning tests. **Do not record test
  counts or other figures that go stale as live-status in `STATUS.md`** — "tests pass" and
  "the system ran clean" are the signals that matter.
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
executor (only trivial typo-level changes inline); (4) that you write the change dir
continuously but reconcile `STATUS.md`/`ai-docs/` only at `/opsx:archive`, preferably in
a fresh session.
