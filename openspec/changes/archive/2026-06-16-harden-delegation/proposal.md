## Why

Delegated work — the deepseek apply-executor and the deepseek reviewer — is currently governed by *trust* ("we asked the agent to run the tests / not to spin") and a fixed wall-clock timeout. Three observed timeouts expose the gaps: (1) an apply-executor looped — 12 edits to one test file, the same tests failing — and burned the full 10-min cap; (2) a reviewer spent its entire 5-min budget on read-only exploration and produced **no review**; (3) separately, green mock suites have shipped broken integrations because nothing *deterministically* enforces "tests pass before commit." These are closed by deterministic gates and a defined stop condition — not by larger timeouts or more trust.

## What Changes

- **Commit-time test gate (deterministic).** Add a Claude Code `PreToolUse` hook on `git commit` that runs a shared `scripts/test-gate.sh` and **blocks the commit** if the project's tests are not green. The apply-executor never commits, so the orchestrator's commit is the single chokepoint — gating it makes "tests green before commit" non-bypassable regardless of how the apply ran. The hook calls one shared script; the per-repo test command is the only per-repo value.

- **Apply-executor: bounded-retry-then-report, with a DEFINED non-convergence stop condition.** The executor still does healthy `write → test → fix` iteration, but it **stops and reports the blocker** (instead of continuing to edit) the moment it hits *non-convergence*, defined as ANY of:
  - the same failing test still fails with the **same error signature after 2 consecutive fix attempts** aimed at it (progress = the error changes; spin = the error stays the same);
  - it is about to edit the **same file a 3rd time** to resolve the **same** failure;
  - the fix requires information or a decision **absent from `tasks.md`/`design.md`/`proposal.md`**, requires **modifying `proposal.md`/`design.md`** (outside executor remit), or an **external API/library behaves contrary to `design.md`**.

  On any trigger the executor stops editing, writes a completion report naming the specific blocker (which test, the error signature, attempts made, what is missing), and **recovery becomes the orchestrator's job** — re-plan, tighten the brief, dispatch a *fresh* executor, or escalate to the user. Tactical local fixes stay with the executor; this fires only on genuine non-convergence, not on the first red test.

- **Apply skill failure ladder is modified to act on the new signal.** Today the ladder (openspec-apply-change, step 6.4) routes any "Non-crash failure" (tasks left `[ ]` / "got stuck") to an **immediate Sonnet subagent**. This splits: a **diagnosed non-convergence blocker** (the executor followed the stop rule and named the blocker) goes to **orchestrator triage** — re-plan / tighten brief / fresh executor / escalate, *which may still choose Sonnet* if the cause is model capability rather than a brief/plan gap; an **opaque give-up** (no useful blocker) keeps today's immediate-Sonnet behavior. This prevents throwing a more expensive model at the same flawed plan.

- **Reviewer: budget for thoroughness, not speed.** Raise the `openspec-reviewer` runtime cap (currently 300s — half the apply budget) and have the reviewer **append findings to `review-log.md` incrementally**, so a cutoff yields a usable partial review instead of nothing. No read/grep throttle — re-examining a file or re-searching a symbol on new information is legitimate review behavior.

- **Explicit non-goals** (decided against in exploration; recorded so they are not re-litigated):
  - **No progress-heartbeat / stall-on-idle kill.** The observed loops kept tool activity *continuous*, so activity-based stall detection would have caught at most 1 of the 3 cases while adding false-kill risk to legitimate long single operations (e.g. running the test suite).
  - **Raising the apply wall-clock cap is not the primary fix.** For a looping run a larger cap just wastes more time before failing; the cap stays a backstop.
  - **The OpenCode-side test-gate plugin is deferred (v2).** The Claude `PreToolUse` hook is the v1 enforcement point; an OpenCode plugin that runs the gate on the executor is out of scope here — its event system may sit behind an experimental flag and `tool.execute.after` is documented-but-unproven, so it needs a smoke test first.
  - **`--no-verify` bypass is an accepted residual risk.** A `PreToolUse` git-commit hook can be bypassed with `git commit --no-verify`. We accept this for v1 (the gate is a strong default against accidental red commits, not an adversarial control); a secondary guard (post-commit / CI) is out of scope.

## Capabilities

### New Capabilities
- `commit-test-gate`: deterministic enforcement that the project's tests pass before any orchestrator commit, via a harness hook that calls a shared gate script.
- `apply-convergence-guard`: the apply-executor's bounded-retry behavior and the defined non-convergence stop-and-report condition that hands recovery to the orchestrator.
- `reviewer-budget`: the reviewer's runtime budget and incremental-output behavior that protect review thoroughness from timeout starvation.

### Modified Capabilities
<!-- none — openspec/specs/ is currently empty (this change introduces the first specs) -->

## Impact

- **Skills / agents (golden source, openspec-scaffold):**
  - `.claude/skills/openspec-apply-change` — failure-ladder split (non-convergence → orchestrator triage).
  - `.claude/agents/apply-executor.md` + `.opencode/agents/apply-executor.md` — the bounded-retry / non-convergence stop rule.
  - `.claude/skills/openspec-propose` — reviewer invocation (raised timeout) and incremental review-log behavior.
  - `.opencode/agents/openspec-reviewer.md` — incremental-output behavior (and, pending the design decision, edit permission scoped to `review-log.md`).
  - `.claude/skills/openspec-verify-change` — the commit gate fires on the orchestrator's **verify-time commit**, so the verify skill must reference/expect it (it enforces what verify already requires).
- **New files:** `scripts/test-gate.sh`; a `.claude/settings.json` `hooks` block; a per-repo test-command value the gate reads.
- **Cross-tool:** the Claude `PreToolUse` hook is the v1 enforcement point; the OpenCode-side plugin is a deferred v2 (see Explicit non-goals).
- **Downstream:** these new/edited files are shared assets; the forthcoming **single-source** change will fold them into its sync manifest (out of scope here). No application code is touched; the scaffold itself has no tests, so the gate is a no-op in the scaffold and only bites in consuming repos (extrends / psc-monitor).
