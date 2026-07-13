---
name: openspec-apply-change
description: Implement tasks from an OpenSpec change. Use when the user wants to start implementing, continue implementation, or work through tasks.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Implement tasks from an OpenSpec change.

> **MANDATORY — delegation override. Read before Step 6; it changes who implements.**
> Per `AGENTS.md` and `openspec/config.yaml` `rules.tasks`, the primary agent does **not** implement tasks inline. Delegate implementation to the **apply-executor**:
> - **Claude Code:** drive the OpenCode `apply-executor` (deepseek-v4-flash) via `opencode run` (see Step 6 for the exact invocation and the failure ladder). A Sonnet subagent is used **only as a fallback** per that ladder. Do **not** make a Sonnet subagent the default, and do **not** implement inline.
> - **OpenCode:** delegate to `@apply-executor` (DeepSeek V4 Flash) as today — unchanged.
>
> Step 6 below ("Make the code changes required") therefore describes what the **apply-executor** does — not the primary. The primary's job is to delegate, then review the executor's completion report and proceed to verify (its own behavioral review). The primary must not write implementation code itself (trivial typo / one-line exception only).

**PHASE GATE — STOP after implementation.** Once all tasks are checked off, without an explicit autonomy grant this is a hard STOP: tell the user "All tasks complete. Say 'verify <name>' when you want me to review the implementation." Then WAIT. Under an autonomy grant, auto-advance to verify is permitted per the `autonomy-phase-advance` canonical rule (AGENTS.md) EXCEPT across a premise DISSENT, an unresolved verify NEEDS-REVISION, or an operator-named gate — halt and surface to the operator instead of advancing in those cases.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` to get available changes and use the **AskUserQuestion tool** to let the user select

   Always announce: "Using change: <name>" and how to override (e.g., "apply <other>").

1a. **SMALL premise gate (fail-fast after change selection)**
    For a SMALL change, assert that `premise-review.md` exists in the change/plan directory
    and contains a resolved verdict — `PREMISE: AGREE` or a recorded `OVERRIDE: proceed` —
    before proceeding to implementation. If neither is present, STOP with an error: the
    premise pass must complete before apply can begin. MEDIUM/COMPLEX changes skip this gate
    (they received premise review during propose). The apply skill does **not** invoke the
    premise reviewer — the orchestrator already did (see the AGENTS.md SMALL bullet for the
    invocation).

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - `planningHome`, `changeRoot`, and `actionContext`: planning scope and edit constraints
   - Which artifact contains the tasks (typically "tasks" for spec-driven, check status for others)

3. **Get apply instructions**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   This returns:
   - `contextFiles`: artifact ID -> array of concrete file paths (varies by schema - could be proposal/specs/design/tasks or spec/tests/implementation/docs)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest re-running the openspec-propose skill to create the missing artifacts
   - If `state: "all_done"`: congratulate, suggest archive
   - Otherwise: proceed to implementation

   **Workspace guard:** If status JSON reports `actionContext.mode: "workspace-planning"` and `allowedEditRoots` is empty, explain that full workspace apply is not supported in this slice. Treat linked repos and folders as read-only context, ask the user to select an affected area through an explicit implementation workflow, and STOP before editing files.

4. **Read context files**

   Read every file path listed under `contextFiles` from the apply instructions output.
   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, design, tasks
   - Other schemas: follow the contextFiles from CLI output

5. **Show current progress**

   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI

6. **Implement tasks (loop until done or blocked)**

   The delegation path depends on which agent platform you are:

   ---
   ### If you are Claude Code

   Drive the deepseek `apply-executor` via `opencode run` (harness contract:
   `.claude/skills/_shared/delegation-harness.md`); on a clean run every `tasks.md` item is `[x]`
   and you proceed to Step 7. Everything below handles the ways that can fail.
   Do **not** implement tasks yourself, and do **not** spawn a Sonnet subagent as
   the default — use the deepseek executor first.

    1. **Invoke the executor** (substitute real `<changeRoot>` paths), capturing
       stdout and stderr to separate files. See `.claude/skills/_shared/delegation-harness.md` §a–d
       for the shared harness contract (hardened invocation, assert-ran, bounded wait,
       EXIT-sentinel); budgets are in that doc's table (§e).

       ```bash
       timeout -k 30 600 opencode run \
         --dir <repoRoot> \
         --agent apply-executor \
         --model deepseek/deepseek-v4-flash \
         --format json \
         "Implement the OpenSpec change in <changeRoot>. Work <changeRoot>/tasks.md \
          sequentially, top to bottom, following <changeRoot>/design.md and \
          <changeRoot>/proposal.md. Check off each task ([ ] -> [x]) in tasks.md as it \
          lands. Do not modify proposal.md or design.md. Do not commit. End with a brief \
          completion report (what was implemented, deviations, what the primary should \
          check at verify, and any external-API behavior you ASSUMED rather than verified)." \
         > /tmp/apply-out.jsonl 2> /tmp/apply-err.log < /dev/null; \
       echo "EXIT=$?" > /tmp/apply-out.exit
       ```

      **Caveats on invocation:**
      - The OpenCode agent edits files in the **same working tree** as Claude,
        so its `tasks.md` check-offs and source edits land directly on disk —
        read them back via `git diff` and re-read `tasks.md` afterward.
      - If the user named a different executor model, substitute it for
        `deepseek/deepseek-v4-flash`.
      - **Bounded wait + EXIT-sentinel (§c–d):** Run this Bash call with
        `run_in_background: true`; detect completion via `[ -f /tmp/apply-out.exit ]`.
        A premature retry or Sonnet fallback spawns CONCURRENT writers on the same
        working tree (this has left duplicate work) — which is exactly why completion
        must be judged from the sentinel, not guessed from process state. If the wrapper
        fires (exit 124/137 in the exit file), the apply **timed out** — treat it as an
        **operational crash** (see Failure modes). For a very large change, prefer splitting
        delegation across task ranges over raising the ceiling. **Why split:** the executor's
        hard timeout budget (~600s) is the ceiling on any single invocation — splitting keeps
        each run within budget, not to create intermediate review checkpoints. Between slices
        the primary reads `git diff` and runs targeted tests as a smoke (crash/blocker
        detection only, not a behavioral review); the real behavioral review happens at verify.
        If your diff-read finds a defect in slice N, fold the scoped fix as the **first item
        of slice N+1's brief** instead of a separate fix run (sequential, no concurrent
        writers, one fewer invocation).
        **Delegation cue** (cites `delegation-by-default`, AGENTS.md): the between-slice
        git-diff read + targeted-test smoke is run+extract work delegable to a haiku/Sonnet
        subagent — the primary still judges the distilled result.

    2. After the executor (deepseek or Sonnet) finishes, read `tasks.md` and
       `git diff` to confirm all tasks are checked off and changes are on disk.
       Proceed to Step 7.

   #### Failure modes

   If the run doesn't cleanly land every task, triage it:

   1. **Assert the real executor ran (§b):** grep `/tmp/apply-err.log` for
      `Falling back to default agent` — if found, treat as an **operational crash**
      (ladder below). Extract the completion report:
      `grep '"type":"text"' /tmp/apply-out.jsonl | tail -1 | jq -r '.part.text'`
      Empty/unparseable → operational crash. Confirm the extracted text is a non-empty
      completion summary (not a fallback message).

   2. **Determine success vs. failure** by reading back from disk (not just the report):

      - **Success** = the real agent ran AND every task in `tasks.md` is `[x]` AND
        the completion report does not declare an unresolved blocker.
      - **Operational crash** = non-zero exit (including a `timeout` kill — exit
        124, or 137 if SIGKILL was needed), empty/unparseable stdout, or the
        fallback-warning match from the assert-ran step.
      - **Non-crash failure** = real agent ran, but tasks remain `[ ]` / the report
        says it got stuck / output shows it gave up.
        **Distinguish** whether the completion report contains a declared blocker
        by grepping for the literal heading `### NON-CONVERGENCE BLOCKER`:
        (Grep the extracted completion report, never the raw jsonl — the raw stream
        contains the executor's tool-reads of this SKILL.md, including the heading,
        and would false-positive.)

        ```bash
        extracted_text=$(grep '"type":"text"' /tmp/apply-out.jsonl | tail -1 | jq -r '.part.text' 2>/dev/null) || extracted_text=""
        if echo "$extracted_text" | grep -q "### NON-CONVERGENCE BLOCKER" 2>/dev/null \
           || grep -q "### NON-CONVERGENCE BLOCKER" /tmp/apply-err.log 2>/dev/null; then
          echo "DECLARED_BLOCKER"
        else
          echo "OPAQUE_GIVE_UP"
        fi
        ```

        **Delegation cue** (cites `delegation-by-default`, AGENTS.md): the jsonl-parse/extract
        steps above (completion-report extraction, blocker-heading grep) are run+extract work
        delegable to a haiku/Sonnet subagent — OW-7 will later mechanize this entirely; this cue
        is the interim rule.

   3. **Failure ladder:**

      - **Operational crash** → **retry the `opencode run` once** (if it timed out,
        retry with a **tight brief**: name the exact files to read, front-load the facts
        you've already verified as given, and forbid codebase re-exploration — the wrapper
        is a hard ceiling and the executor otherwise burns its budget re-deriving context
        you already have). Second crash → spawn a **Sonnet subagent**
        apply-executor (`Agent` tool, `subagent_type: "apply-executor"`) to finish
        `tasks.md`.
      - **Non-crash failure — declared blocker** (the completion report contains
        `### NON-CONVERGENCE BLOCKER`) → route to **orchestrator triage**, NOT
        reflexive Sonnet. Triage options:
        - *Brief/plan gap* → tighten the brief and dispatch a **fresh** executor
          (not the same one — a new invocation with the amended brief).
        - *Artifact/decision gap* → escalate to the user.
        - *Model-capability gap* → spawn a **Sonnet** subagent (only when the
          blocker's cause is the model itself, not the plan).
      - **Non-crash failure — opaque give-up** (no `### NON-CONVERGENCE BLOCKER`
        heading) → **immediately** spawn the Sonnet subagent apply-executor
        (no retry; identical to the pre-change behavior).
      - **Mandatory disclosure:** whenever Sonnet runs, the primary's completion
        output in Step 7 MUST state (a) the deepseek/opencode failure and how it
        manifested, and (b) that Sonnet finished the work.

   ---
   ### If you are OpenCode

   Delegate the whole `tasks.md` loop to `@apply-executor` (DeepSeek V4 Flash)
   via the Task tool with `subagent_type: "apply-executor"` — unchanged from
   existing behavior.

   For each pending task:
   - Show which task is being worked on
   - Make the code changes required
   - Keep changes minimal and focused
   - Mark task complete in the tasks file: `- [ ]` → `- [x]`
   - Continue to next task

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - **Error or blocker encountered** → inspect the executor output for a
     `### NON-CONVERGENCE BLOCKER` heading:
     - **Declared blocker found** → report it to the user with the triage
       options (tighten brief + fresh executor / escalate to user for
       artifact/decision gap / Sonnet only if model-capability gap).
     - **No declared blocker** (opaque give-up) → dispatch a **fresh**
       `@apply-executor` (do NOT route to Sonnet), or escalate to the user
       if another retry is unlikely to help.
   - User interrupts

7. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all done: suggest archive
   - If paused: explain why and wait for guidance

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)

Working on task 3/7: <task description>
[...implementation happening...]
✓ Task complete

Working on task 4/7: <task description>
[...implementation happening...]
✓ Task complete
```

**Output On Completion**

```
## Implementation Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓

### Completed This Session
- [x] Task 1
- [x] Task 2
...

**Executor:** deepseek-v4-flash via `opencode run`
**Fallback used:** No

All tasks complete! Say 'verify <name>' to review the implementation, or 'archive <name>' to archive.
```

When a fallback to Sonnet occurred, replace the **Executor** / **Fallback used** lines with:

```
**Executor:** deepseek-v4-flash via `opencode run` (FAILED — <brief description of how>)
**Fallback used:** Yes — Sonnet subagent completed the work.
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**
- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- **Before marking a task done, run `ruff check --fix` and `ruff format` on every Python file the executor created or edited (the executor autofix habit — see the apply-executor agent rules).**
- **PHASE GATE**: When implementation is complete, without an autonomy grant this is a hard STOP — inform the user and prompt them for the next step. Under a grant, auto-advance to verify per the `autonomy-phase-advance` rule (AGENTS.md), EXCEPT across a premise DISSENT, an unresolved verify NEEDS-REVISION, or an operator-named gate.
- Update task checkbox immediately after completing each task
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
