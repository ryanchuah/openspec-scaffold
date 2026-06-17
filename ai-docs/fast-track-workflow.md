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
  - Failure ladder: follow the apply skill's ladder in `.claude/skills/openspec-apply-change/SKILL.md` — operational crash → retry once → Sonnet; non-crash → a declared blocker (`### NON-CONVERGENCE BLOCKER`) routes to orchestrator triage (NOT reflexive Sonnet), an opaque give-up → Sonnet. Always disclose any fallback.
- **Verify is always real.** Even a SMALL change requires a diff read, a behavioral test, and the flash verifier pass. Never mark a change done off a green test suite alone.
- **Archive runs normally.** For MEDIUM and COMPLEX, archive per the normal archive skill — do not skip it.
- **Executors never commit.** You review the diff, then you commit. Pushes to `main` still require explicit operator authorization.
