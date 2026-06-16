---
name: openspec-verify-change
description: Verify implementation matches change artifacts. Use when the user wants to validate that implementation is complete, correct, and coherent before archiving.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Verify that an implementation matches the change artifacts (specs, tasks, design).

> **MANDATORY — behavioral review. This is the core of verify, not optional, and runs BEFORE the artifact/spec checklist below.**
> Per `AGENTS.md` and `openspec/config.yaml`, verifying a change is the orchestrator's own review of the apply-executor's work — a substantive behavioral review, not a checklist rubber-stamp. Before generating the verification report, the main agent MUST itself do all of the following — do not delegate this, and do not trust the executor's completion summary:
>
> 1. **Read the actual diffs and changed files.** Run `git diff` (and open the files) for everything the executor touched. Trust the code, not the summary.
> 2. **Re-run the FULL test suite yourself:** `.venv/bin/python -m pytest -q`. It must be green (pre-existing skips OK). A green exit is **necessary but not sufficient.**
>    **Note:** The commit-test-gate (`.claude/settings.json` `PreToolUse` hook on
>    `git commit`) backstops this requirement — it blocks any commit whose tests
>    are not green. A failing verify should be caught BEFORE the gate would block,
>    making the gate the known last-resort enforcement rather than the first line.
> 3. **Eyeball the real output the code produces.** Render a concrete sample of what the change actually generates — the actual records/rows selected, the text or prompt produced, the request sent, the values computed — not just that tests pass. Run the relevant project command or a `scripts/_*_oneoff.py` probe against real data and inspect a real sample. Bugs that logic-reading misses are often visible the instant you render real output.
> 4. **If the change touches an external API / network service, RUN ITS LIVE SMOKE yourself against the real endpoint.** The mock-based suite is *structurally blind* to whether the mocks match reality — a fully green suite can encode a **wrong** API contract (wrong sort semantics, wrong field types, wrong error codes) and so pass while the real integration collects nothing. This has already happened on real projects: an integration shipped with wrong sort semantics and a 500-ing backfill, with mocks that encoded the *idealized* API, so a fully green suite passed over a non-functional integration. Therefore: run the change's opt-in live test (e.g. `LIVE_TESTS=1 .venv/bin/python -m pytest tests/test_<x>.py -k live -v`) and inspect a real response. **A *skipped* live smoke is NOT a *passed* one.** If an external-API change has no live smoke at all, that is itself a **CRITICAL** gap — require one to be added before archive.
> 5. **On any defect:** diagnose and scope it yourself (reproduce it, run DB queries, read diffs), then **re-delegate the fix to a FRESH apply-executor** with a self-contained fix-spec that cites the exact file:line evidence and the concrete fix. Do **not** hand-fix beyond a trivial typo / comment / one-line rename — if you would write more than ~2 lines of implementation, stop and re-delegate. Then re-verify from step 1.
>    - **Claude Code:** the fresh fix executor is the deepseek `apply-executor` driven via `opencode run` (same invocation shape as in the apply skill's Step 6, but the prompt is the **self-contained fix-spec** for the specific defect, not the whole `tasks.md`). **One attempt.**
>    - **Wrap the call in `timeout -k 15 300 opencode run …`** (a scoped single-defect fix should finish well inside 5 minutes). The wrapper kills **only the opencode process it launched** — other concurrent opencode processes are untouched and no children are orphaned. **Never** `pkill`/`killall opencode`. A `timeout` kill (exit 124, or 137 if SIGKILL was needed) counts as the operational failure in the next bullet → escalate to Sonnet.
>    - **Completion detection — EXIT-file sentinel, never process liveness (binding).** Append `; echo "EXIT=$?" > /tmp/fix-out.exit` to the wrapped command, run it with `run_in_background: true`, and detect completion by `[ -f /tmp/fix-out.exit ]` (or the harness background-completion notification). **NEVER poll with `pgrep -f "<pattern>"`** (it self-matches the poller's own command line) and **never judge a run from a mid-execution jsonl snapshot** — a slow run is NOT a crash. Conclude crash ONLY if the exit file shows nonzero/124/137, OR no opencode PID remains AND no exit file was ever written. Also note: scoped fix runs have repeatedly completed their work and still exited 1 at session teardown — judge success from disk (`git diff`, tests), not the exit code alone.
>    - Reuse the same "assert the real agent ran" checks (fallback-warning grep + parseable output).
>    - **Escalate to a Sonnet subagent** if that one attempt yields **either**: (a) an operational failure (crash / no usable output), **or** (b) a quality failure — i.e. the orchestrator's re-verification (re-run from MANDATORY step 1) still finds the defect, or finds a newly-introduced one.
>    - After Sonnet fixes it, re-verify again from step 1.
>    - **Mandatory disclosure:** if Sonnet was used, say so in the verification report / `notes.md` field 3 ("defect found and how it was fixed — and who fixed it"), explicitly noting the deepseek attempt failed and Sonnet took over.
>
> Only after this behavioral review passes, proceed to the artifact/spec mapping checks below and emit the report. If the behavioral review fails, the verdict is **NEEDS REVISION** regardless of the checklist.

**PHASE GATE — STOP after verification.** Once the verification report and `notes.md` checkpoint are complete, you MUST NOT automatically proceed to archive. Tell the user the verdict and prompt them: "Verification complete. Say 'archive <name>' when ready to archive." Then WAIT. Never invoke archive without an explicit user request. Crossing phases without permission is a hard rule.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show changes that have implementation tasks (tasks artifact exists).
   Include the schema used for each change if available.
   Mark changes with incomplete tasks as "(In Progress)".

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context
   - Which artifacts exist for this change

   If status reports `actionContext.mode: "workspace-planning"`, explain that full workspace implementation verification is not supported in this slice and STOP. Do not infer repo-local implementation ownership or edit linked repos.

3. **Get planning context and load artifacts**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   This returns the change directory and `contextFiles` (artifact ID -> array of concrete file paths). Read all available artifacts from `contextFiles`.

4. **Initialize verification report structure**

   Create a report structure with three dimensions:
   - **Completeness**: Track tasks and spec coverage
   - **Correctness**: Track requirement implementation and scenario coverage
   - **Coherence**: Track design adherence and pattern consistency

   Each dimension can have CRITICAL, WARNING, or SUGGESTION issues.

5. **Verify Completeness**

   **Task Completion**:
   - If `contextFiles.tasks` exists, read every file path in it
   - Parse checkboxes: `- [ ]` (incomplete) vs `- [x]` (complete)
   - Count complete vs total tasks
   - If incomplete tasks exist:
     - Add CRITICAL issue for each incomplete task
     - Recommendation: "Complete task: <description>" or "Mark as done if already implemented"
   - **Note:** by convention `tasks.md` holds apply-phase work ONLY (no verify/archive
     checkboxes), so an incomplete task genuinely means implementation work remains — CRITICAL
     is correct. The change-specific acceptance criteria you verify behaviorally against live
     in design.md's **Verification** section, not in `tasks.md`.

   **Spec Coverage**:
   - If delta specs exist in `contextFiles.specs`:
     - Extract all requirements (marked with "### Requirement:")
     - For each requirement:
       - Search codebase for keywords related to the requirement
       - Assess if implementation likely exists
     - If requirements appear unimplemented:
       - Add CRITICAL issue: "Requirement not found: <requirement name>"
       - Recommendation: "Implement requirement X: <description>"

6. **Verify Correctness**

   **Requirement Implementation Mapping**:
   - For each requirement from delta specs:
     - Search codebase for implementation evidence
     - If found, note file paths and line ranges
     - Assess if implementation matches requirement intent
     - If divergence detected:
       - Add WARNING: "Implementation may diverge from spec: <details>"
       - Recommendation: "Review <file>:<lines> against requirement X"

   **Scenario Coverage**:
   - For each scenario in delta specs (marked with "#### Scenario:"):
     - Check if conditions are handled in code
     - Check if tests exist covering the scenario
     - If scenario appears uncovered:
       - Add WARNING: "Scenario not covered: <scenario name>"
       - Recommendation: "Add test or implementation for scenario: <description>"

7. **Verify Coherence**

   **Design Adherence**:
   - If `contextFiles.design` exists:
     - Extract key decisions (look for sections like "Decision:", "Approach:", "Architecture:")
     - Verify implementation follows those decisions
     - If contradiction detected:
       - Add WARNING: "Design decision not followed: <decision>"
       - Recommendation: "Update implementation or revise design.md to match reality"
   - If no design.md: Skip design adherence check, note "No design.md to verify against"

   **Code Pattern Consistency**:
   - Review new code for consistency with project patterns
   - Check file naming, directory structure, coding style
   - If significant deviations found:
     - Add SUGGESTION: "Code pattern deviation: <details>"
     - Recommendation: "Consider following project pattern: <example>"

8. **Generate Verification Report**

   **Summary Scorecard**:
   ```
   ## Verification Report: <change-name>

   ### Summary
   | Dimension    | Status           |
   |--------------|------------------|
   | Completeness | X/Y tasks, N reqs|
   | Correctness  | M/N reqs covered |
   | Coherence    | Followed/Issues  |
   ```

   **Issues by Priority**:

   1. **CRITICAL** (Must fix before archive):
      - Incomplete tasks
      - Missing requirement implementations
      - Each with specific, actionable recommendation

   2. **WARNING** (Should fix):
      - Spec/design divergences
      - Missing scenario coverage
      - Each with specific recommendation

   3. **SUGGESTION** (Nice to fix):
      - Pattern inconsistencies
      - Minor improvements
      - Each with specific recommendation

   **Final Assessment**:
   - If CRITICAL issues: "X critical issue(s) found. Fix before archiving."
   - If only warnings: "No critical issues. Y warning(s) to consider. Ready for archive (with noted improvements)."
   - If all clear: "All checks passed. Ready for archive."

9. **Checkpoint verify findings to the change dir (MANDATORY before archive handoff)**

   After emitting the report and BEFORE telling the user to run archive, append the verification
   outcome to the change's `notes.md` (`<changeRoot>/notes.md`). You MUST capture **all five** of the
   following — treat each as a required field, and if one is genuinely empty, write "none" plus one
   line of *why*, never silently omit it:

   1. the **verdict** (ready for archive / needs revision);
   2. **what you confirmed by eyeballing live output** during the behavioral review — recorded as
      behavior, not counts (e.g. "collect_recent stored docs but every body came back empty; board
      surfaced the expected <terms>"). The eyeball itself stays mandatory; only the figures are
      barred — **never** test, doc, or row counts, not even as history (see AGENTS.md);
   3. any **defect found and how it was fixed** (and who fixed it — re-delegated executor vs trivial
      inline);
   4. any **as-built delta discovered during verify** that the artifacts don't already record;
   5. **forward-looking items for the project docs — the load-bearing, easily-missed one.** Enumerate
      every **open question, tuning item, deferred-scope decision, follow-on, or monitored risk** that
      surfaced during design OR verify and is **recorded nowhere else** (not in `proposal.md` /
      `design.md` / `specs/` and not already in `ai-docs/open-questions.md`). These exist to be folded
      into `ai-docs/open-questions.md` (and where relevant `ai-docs/decisions.md`) at archive. Be
      exhaustive — typical sources you MUST scan for:
        - **"tune after real runs" items** — any new threshold/default/knob this change introduced that
          has not been validated against real production output (e.g. a new config default);
        - **observations from the live-output eyeball** that imply a *future question* even when current
          behavior is correct-by-design (e.g. "monitor is collapse-only; a live surge was observed —
          do we want symmetric monitoring?");
        - **scope deferrals** stated in design Non-Goals/Risks that the operator will plausibly ask
          about later (alerting, second-order risks, follow-on phases);
        - anything you said "out of scope / revisit later / could add" about during this session.

   Also write a short **"Still owned by archive"** pointer list (what the fresh archive session
   must still reconcile: `STATUS.md`, `ai-docs/decisions.md`, `ai-docs/open-questions.md`, spec
   promotion into `openspec/specs/`, and any cleanup). Do NOT edit those project-tracked docs yourself
   here — they are reconciled at archive per the write-discipline rule; your job at verify is to make
   the change dir self-sufficient so that reconciliation loses nothing.

   Why this is mandatory: per `AGENTS.md`, archive is reconciled by a **delegated
   deepseek-v4-pro archive-executor (fresh context), then primary-reviewed**. That executor reads
   the change dir, not this conversation. Verify is the step that manufactures these durable facts,
   and anything left only in this context **dies at the session boundary** — the archive-executor
   is blind to it. **Field 5 is the one that bites:** a new open-question or tuning item that
   exists only in this conversation is simply *lost* — it never reaches `open-questions.md`, and
   the project silently forgets a decision it meant to revisit. This write is cheap because the
   context is already loaded. Do not skip it even when the verdict is a clean pass.

10. **Verbally acknowledge documentation persistence (MANDATORY — do not end the turn without it)**

    After writing `notes.md`, you MUST close your response to the user with an explicit, itemised
    acknowledgement that confirms each required `notes.md` field was persisted. This is a forcing
    function: stating it out loud catches the silent-omission failure that field 5 is most prone to.

    Use exactly this shape (fill in the real content; do not paraphrase the labels away):

    ```
    ✅ Documentation persisted to <changeRoot>/notes.md:
      1. Verdict — <ready for archive / needs revision>
      2. Live output eyeballed — <one-line pointer to the real sample recorded>
      3. Defects + fixes — <summary, or "none">
      4. As-built deltas — <summary, or "none">
      5. Forward-looking open-questions / tuning items / follow-ons — <explicit list, or "none + why">
      Still owned by archive — <STATUS.md, decisions.md, open-questions.md, spec promotion, cleanup>
    ```

    For field 5 you MUST either **name each item** carried forward (so the user can sanity-check that
    nothing was dropped) or state "none" with a one-line justification. A bare "docs updated" or
    "ready for archive" WITHOUT this itemised confirmation is non-compliant — losing an open-question
    or tuning item to the session boundary is a critical documentation failure, and this step exists to
    make that failure impossible to commit silently.

**Verification Heuristics**

- **Completeness**: Focus on objective checklist items (checkboxes, requirements list)
- **Correctness**: Use keyword search, file path analysis, reasonable inference - don't require perfect certainty
- **Coherence**: Look for glaring inconsistencies, don't nitpick style
- **False Positives**: When uncertain, prefer SUGGESTION over WARNING, WARNING over CRITICAL
- **Actionability**: Every issue must have a specific recommendation with file/line references where applicable

**Graceful Degradation**

- If only tasks.md exists: verify task completion only, skip spec/design checks
- If tasks + specs exist: verify completeness and correctness, skip design
- If full artifacts: verify all three dimensions
- Always note which checks were skipped and why

**Output Format**

Use clear markdown with:
- Table for summary scorecard
- Grouped lists for issues (CRITICAL/WARNING/SUGGESTION)
- Code references in format: `file.ts:123`
- Specific, actionable recommendations
- No vague suggestions like "consider reviewing"
- **PHASE GATE**: When verification is complete, STOP. Inform the user and prompt them for the next step. Never invoke archive without an explicit user request. This is a hard rule.
