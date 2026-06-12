# Fast-Track Workflow (trusted agents only)

> **STOP AND READ THIS GATE BEFORE PROCEEDING.**
>
> This is an **opt-in override** for high-capability agents that the operator — the human directing this work — explicitly trusts to iterate with minimal human checkpoints. It exists because such agents need fewer checks and balances to produce correct output.
>
> **The default for every agent is the normal OpenSpec workflow** (AGENTS.md + the openspec-* skills). This file does not replace that default — it overrides it only when the operator says so.
>
> You may use the shortcuts in this file **only if the operator has explicitly granted you fast-track authority** for this session or task.
>
> **If you are reading this without that explicit grant: stop, ignore this file, and use the normal workflow.**

---

## Operating under fast-track

Once granted, you proceed **autonomously** — work through the workflow's normal interactive checkpoints without pausing to ask the operator for confirmation, using your own judgment at each step. The entire point is full execution without per-step prompting.

**Still stop and ask the operator when:**
- A requirement is genuinely ambiguous and you cannot make a safe default call.
- An action is irreversible or destructive (data loss, force-push, deleting non-restorable work).

**Always disclose** what you did: the tier you assigned, any delegations made, and any fallbacks taken.

---

## Classify each change (you decide)

You classify each change yourself into one of the three tiers below. State the classification explicitly at the start of your work. Only ask the operator if you are genuinely unsure which tier applies.

---

## The three tiers

### SMALL — skip OpenSpec entirely

You must still do all of the following:

1. **Write a short plan** and checkpoint it to `plans/<slug>-plan.md`. This file doubles as the executor's instruction sheet.
2. **Delegate execution** to the apply-executor (`deepseek/deepseek-v4-flash` via `opencode run` under Claude Code; `@apply-executor` under OpenCode). Do not implement inline.
3. **Verify the result yourself** — read the diff and run a behavioral test. A green test suite alone does not count as verification.

### MEDIUM — official OpenSpec lifecycle, with one trim

Run the full OpenSpec lifecycle with one permitted shortcut: the propose phase may emit **only `tasks.md`** (no `proposal.md`, no `design.md`, no spec delta files).

Rules that still apply in full:
- The `tasks.md` is **still reviewed by the `deepseek/deepseek-v4-pro` reviewer before freeze**.
- Because there is no `design.md` to hold them, change-specific **verify acceptance criteria go in the change's `notes.md`**.

**Escape hatch:** if a genuine design decision surfaces mid-flight, stop immediately. Either ask the operator or promote the change to the full COMPLEX process. Never bury a real design decision inside `tasks.md`.

### COMPLEX / UNCERTAIN — full OpenSpec lifecycle

Run the full lifecycle per the skills: explore → propose → apply → verify → archive. No shortcuts.

When in doubt between tiers, classify up.

---

## Guardrails that never relax

These apply regardless of tier.

- **You are the orchestrator/reviewer, not the implementer.** No hand-written implementation code beyond a single trivial one-liner — and that exception must be disclosed every time. Execution is always delegated to the apply-executor.

- **Delegation mechanics are identical to the normal workflow:**
  - Use the same `opencode run` executor/reviewer invocations.
  - Assert that the real agent actually ran (do not accept a self-report).
  - Judge success from disk via `git diff` and task check-offs — not the agent's own claim of success.
  - Failure ladder: operational crash → retry once → Sonnet subagent; non-crash failure → Sonnet immediately. Always disclose any fallback taken.

- **Verify is always real.** Even SMALL requires a diff read and a behavioral test. Never mark a change done off a green test suite alone.

- **Archive runs normally.** For MEDIUM and COMPLEX, archive per the normal archive skill. Do not skip it.

- **Executors never commit.** You review the diff, then you commit.

---

## Summary table

| Tier | What you skip | What you must still do |
|---|---|---|
| **SMALL** | All OpenSpec lifecycle artifacts | Write `plans/<slug>-plan.md`, delegate to apply-executor, verify via diff + behavioral test |
| **MEDIUM** | `proposal.md`, `design.md`, spec delta files | Produce `tasks.md`, reviewer freeze, acceptance criteria in `notes.md`, full apply/verify/archive |
| **COMPLEX** | Nothing | Full lifecycle: explore → propose → apply → verify → archive |
