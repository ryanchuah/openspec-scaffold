---
name: openspec-archive-change
description: Archive a completed change in the experimental workflow. Use when the user wants to finalize and archive a change after implementation is complete.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.1"
  generatedBy: "1.4.1"
---

Archive a completed change in the experimental workflow.

**PHASE GATE — archive is the FINAL phase.** When archive completes (move + reconciliation + commit), you are DONE. Do NOT start any new work, propose a new change, or invoke any other workflow skill without an explicit user request. Show the completion summary and stop.

> **MANDATORY — delegation override. Read before Step 5; it changes who executes.**
> After the interactive gates (Steps 1–4), the primary does **not** perform the archive inline.
> Delegate full execution — directory move, optional delta-spec sync, and project-doc
> reconciliation — to the **archive-executor**:
> - **Claude Code:** drive the OpenCode `archive-executor` (deepseek-v4-pro) via `opencode run`
>   (see Step 5 for the exact invocation and the failure ladder). A Sonnet subagent is used
>   **only as a fallback** per that ladder.
> - **OpenCode:** delegate to `@archive-executor` (DeepSeek V4 Pro) via the Task tool.
>
> After the interactive gates the primary first takes a **pre-handoff checkpoint commit**
> (Step 5.0) to snapshot a clean baseline, then delegates. After the executor finishes, the
> **primary reviews** the reconciliation (reads diffs, verifies doc content), fixes anything
> wrong, then **commits**. Executors never commit; if an executor botches the tree, the primary
> restores that baseline before retrying.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show only active changes (not already archived).
   Include the schema used for each change if available.

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Check artifact completion status**

   Run `openspec status --change "<name>" --json` to check artifact completion.

   Parse the JSON to understand:
   - `schemaName`: The workflow being used
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context
   - `artifacts`: List of artifacts with their status (`done` or other)

   If status reports `actionContext.mode: "workspace-planning"`, explain that workspace archive is not supported in this slice and STOP. Do not move workspace changes into repo-local archives or edit linked repos.

   **If any artifacts are not `done`:**
   - Display warning listing incomplete artifacts
   - Use **AskUserQuestion tool** to confirm user wants to proceed
   - Proceed if user confirms

3. **Check task completion status**

   Read the tasks file (typically `tasks.md`) to check for incomplete tasks.

   Count tasks marked with `- [ ]` (incomplete) vs `- [x]` (complete). By convention
   `tasks.md` holds apply-phase work ONLY — verify/archive steps are not tracked there — so
   any incomplete task means implementation work genuinely remains (not a pending doc/spec step). (Rule canonical: `openspec/config.yaml` `rules.tasks`.)

   **If incomplete tasks found:**
   - Display warning showing count of incomplete tasks
   - Use **AskUserQuestion tool** to confirm user wants to proceed
   - Proceed if user confirms

   **If no tasks file exists:** Proceed without task-related warning.

4. **Assess delta spec sync state**

   Use `artifactPaths.specs.existingOutputPaths` from status JSON to check for delta specs. If none exist, proceed without sync prompt.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `openspec/specs/<capability>/spec.md`
   - Determine what changes would be applied (adds, modifications, removals, renames)
   - Show a combined summary before prompting

   **Prompt options:**
   - If changes needed: "Sync now (recommended)", "Archive without syncing"
   - If already synced: "Archive now", "Sync anyway", "Cancel"

   Record whether sync was requested — this is passed to the archive-executor in Step 5.

5. **Delegate archive execution**

   After the interactive gates (Steps 1–4), delegate full execution to the `archive-executor`.
   Compute the target archive path: `<planningHome.changesDir>/archive/YYYY-MM-DD-<name>`.

   **5.0 — Pre-handoff checkpoint (primary; both platforms).** The executor runs with Bash +
   Edit over the whole tree and never commits, so a mistake lands as uncommitted damage. Before
   handing off, snapshot a clean baseline you can return to:

   1. **Verify the tree holds only this change.** Run `git status --porcelain` and confirm every
      *tracked* modification/deletion/rename belongs to the change being archived — `<changeRoot>/`
      or the shared docs/specs the executor will reconcile (knowledge/STATUS.md, knowledge/decisions/INDEX.md,
      knowledge/questions/INDEX.md, `openspec/specs/`). In the serialized apply→verify→archive
      lifecycle every tracked mod must be this change's. If a tracked modification appears OUTSIDE
      that scope, **STOP** and surface it — "another change may be mid-execution; archive expects
      serialized apply→verify→archive." Untracked entries (`??`) under other change dirs are
      expected concurrent propose/explore work and are fine.
   2. **Snapshot the change at HEAD:**
      ```bash
      git commit -am "Checkpoint <name> before archive"
      ```
      This commits ALL *tracked* modifications — the change's full footprint, including any source
      files it touched anywhere in the tree, not just the change dir. `-a` is **required**; do
      **NOT** use `-A` — concurrent propose work is untracked and must be excluded, and `-A` would
      sweep those other changes' artifacts into this commit. It's a no-op if apply already
      committed everything — that's fine.
   3. **The one assumption:** this checkpoint is airtight only if the change has no *untracked new*
      files of its own. That holds because apply commits new files in its reviewed checkpoints, so
      by archive time the change's new files are already tracked; the only untracked files left in
      the tree are other changes' propose artifacts.

   The delegation path depends on which agent platform you are:

   ---
   ### If you are Claude Code

   Drive the OpenCode `archive-executor` (deepseek-v4-pro) via `opencode run`.
   Do **not** perform the archive yourself, and do **not** spawn a Sonnet subagent as
   the default — use the deepseek executor first.

     1. **Invoke the executor** (substitute real paths and the sync decision), capturing
        stdout and stderr to separate files.
        Per `.claude/skills/_shared/delegation-harness.md` §a (hardened invocation): `< /dev/null`
        + `--dir <repoRoot>`. Budget 600s with `-k 30` per the table in §e.
        Note: the archive invocation **omits the EXIT-sentinel** — this is a
        pre-existing drift documented in §d and left as-is.

        ```bash
        timeout -k 30 600 opencode run \
          --dir <repoRoot> \
          --agent archive-executor \
          --model deepseek/deepseek-v4-pro \
          --format json \
          "Archive the OpenSpec change. changeRoot: <changeRoot>. \
           archivePath: <planningHome.changesDir>/archive/YYYY-MM-DD-<name>. \
           Delta spec sync requested: <yes/no>. \
           Project docs: knowledge/STATUS.md, knowledge/decisions/INDEX.md, knowledge/questions/INDEX.md. \
           Move the change dir to the archive path, sync delta specs if requested, \
           and reconcile the three project docs from the archived notes.md / \
           proposal.md / design.md. Also run scripts/knowledge_lint.py and re-check \
           knowledge/reference/, knowledge/roadmap.md, and the individual \
           knowledge/questions/<item>.md Parked bodies for now-stale claims about this \
           just-shipped change; surface any findings flag-only — do not edit those wider \
           bodies. Do not commit. End with a brief completion \
           report (what was moved, which specs synced, which docs reconciled, any \
           wider-sweep findings, anything the primary should double-check)." \
          > /tmp/archive-out.jsonl 2> /tmp/archive-err.log < /dev/null
        ```

        - The OpenCode agent edits files in the **same working tree** as Claude, so
          its moves and doc edits land directly on disk — verify by reading back.
       - **Bounded wait + surgical kill.** Per `.claude/skills/_shared/delegation-harness.md` §c
         (surgical kill — never `pkill`). Because reconciliation can run several
         minutes, run this Bash call with `run_in_background: true`. Exit 124 (or 137
         if SIGKILL was needed) = operational crash (step 4 of the ladder).

    2. **Assert the real executor ran:** Per `.claude/skills/_shared/delegation-harness.md` §b
       (grep stderr for `Falling back to default agent`, extract `part.text` via
       `jq`, confirm parseable). Empty/unparseable → operational crash.

   3. **Judge success from disk** (not just the report):

      - **Success** = the real agent ran AND `<archivePath>/` exists on disk AND
        knowledge/STATUS.md / knowledge/decisions/INDEX.md / knowledge/questions/INDEX.md contain new reconciled content
        AND the report does not declare an unresolved blocker.
      - **Operational crash** = non-zero exit (including a timeout kill — exit 124,
        or 137 if SIGKILL was needed), empty/unparseable stdout, or the
        fallback-warning match.
      - **Non-crash failure** = real agent ran, but the archive dir is missing or
        docs show no new reconciled content.

   4. **Failure ladder:** before retrying the `opencode run` or spawning the Sonnet
      subagent, **restore the baseline** (see the Recovery block at the end of Step 5)
      so each attempt starts from the clean Step 5.0 checkpoint, not a half-botched tree.

      - **Operational crash** → restore the baseline, then **retry the `opencode run`
        once**. Second crash → restore the baseline again, then spawn a **Sonnet
        subagent** archive-executor (`Agent` tool,
        `subagent_type: "archive-executor"`) to complete the archive.
      - **Non-crash failure** → restore the baseline, then **immediately** spawn the
        Sonnet subagent archive-executor (no retry).
      - **Mandatory disclosure:** whenever Sonnet runs, the primary's output in
        Step 7 MUST state (a) the deepseek/opencode failure and how it manifested,
        and (b) that Sonnet finished the work.

   5. After the executor (deepseek or Sonnet) finishes, proceed to Step 6.

   ---
   ### If you are OpenCode

   Delegate the full archive operation to `@archive-executor` (DeepSeek V4 Pro) via
   the Task tool with `subagent_type: "archive-executor"`. Pass:
   - `changeRoot`, target `archivePath`, whether delta spec sync was requested
   - Paths to `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`, `knowledge/questions/INDEX.md`
   - Instruction to also run `scripts/knowledge_lint.py` and re-check `knowledge/reference/`,
     `knowledge/roadmap.md`, and the individual `knowledge/questions/<item>.md` Parked bodies for
     now-stale claims about this just-shipped change, flag-only — surface findings, do not edit
     those wider bodies
   - On executor failure or a botched result, **restore the baseline** (see Recovery below)
     before re-delegating.

   ---
   **Recovery — restoring the baseline after a botched executor run (both platforms).**
   If an executor run leaves the tree partial or wrong (deleted/modified source, half-done `mv`,
   bad reconciliation), restore the pre-handoff baseline BEFORE any retry or re-delegation —
   including before spawning the Sonnet fallback:

   ```bash
   git reset --hard HEAD                                    # reverts all tracked damage; does NOT touch untracked files
   git clean -fd <planningHome.changesDir>/archive/YYYY-MM-DD-<name>   # remove only the partial archive copy
   ```

   Why this is safe with concurrent work: `git reset --hard HEAD` only reverts *tracked* files to
   the Step 5.0 checkpoint and leaves untracked files alone, so concurrent untracked propose work
   survives it; the `git clean` is **path-scoped** to the new archive dir, so it never reaches that
   concurrent work. Hard rules: **never** `git stash`; **never** an unscoped `git clean`; **never**
   recover without having made the Step 5.0 checkpoint — without it, `reset --hard` would discard
   the change's own uncommitted work.

6. **Primary reviews, fixes, and commits**

   Archive is a **handoff**, not just a directory move. The archive-executor runs with
   fresh context (seeded from the change dir and the three project-tracked docs) and
   produces the reconciliation; the primary reviews it before committing.

   - **Read back from disk:** confirm `<archivePath>/` exists, then read the diffs in
     `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`, and `knowledge/questions/INDEX.md`.
   - **Quality check — verify each doc contains real, artifact-backed content:**
     - `knowledge/STATUS.md` `## Latest change` section must record the verify *outcome*
       ("tests pass" / "the system ran clean", or any failing or newly-skipped test
       with its cause) — **never** test, doc, or row counts, not even as history
       (see AGENTS.md) — then link the archive path and name the next concrete step.
     - `knowledge/decisions/INDEX.md` entry must carry the "why" for each key design choice
       with alternatives rejected — not a paraphrase of the problem.
     - `knowledge/questions/INDEX.md` entry must contain ONLY active items (open follow-ons / blockers with **BLOCKING** flags where appropriate); deferred, monitored, or low-priority follow-ons must have been routed to the Parked section of `knowledge/questions/` (per-item files under `##` area headers); and **no live blocker was parked**.
     - `knowledge/STATUS.md` retains at most **3** change paragraphs (`## Latest change` / `## Prior change`) and any overflow is dropped (the oldest section is simply pruned — no separate log file).
   - **Fix trivial issues inline** (wording, missing field, minor formatting).
     For larger gaps — missing reconciliation, fabricated content, wrong structure —
     re-delegate to the archive-executor with a specific fix-spec and re-review.
   - **Lint before committing:** run `python scripts/status_lint.py <repo>` from the
     repo root and resolve any `knowledge/STATUS.md` cap/word-budget or `knowledge/decisions/INDEX.md` Date/Status
     violations it reports (the executor's `#### 3d` step should already have cleaned
     these; this is the primary's gate). If a retained legacy entry trips the budget,
     trim it to a ≤150-word headline (dropping the surplus prose) — before committing.
   - **Commit once satisfied** (the executor never commits; the primary always owns
     the commit):
     ```
     Archive <change-name> and reconcile project docs
     ```
     This can be a single commit or two (archive move + doc reconciliation) — but
     both must be committed before reporting completion.

   **The commit hash chicken-and-egg:** The reconciliation commit produces the hash,
   so the hash cannot be known at reconciliation time. Do NOT include commit hashes
   in reconciled doc entries — reference the change by its archive path (the hash is
   one `git log -- <archive-path>` away). If a prior entry says "commit pending," it
   is a bug from a previous archive — stamp the hash retroactively.

7. **Display summary**

   Show archive completion summary including:
   - Change name
   - Schema that was used
   - Archive location
   - Whether specs were synced (if applicable)
   - Whether project docs were reconciled
   - Executor used (deepseek-v4-pro via `opencode run`, or Sonnet fallback)
   - Note about any warnings (incomplete artifacts/tasks)

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** ✓ Synced to main specs (or "No delta specs" or "Sync skipped")
**Project docs:** ✓ Reconciled (knowledge/STATUS.md, knowledge/decisions/INDEX.md, knowledge/questions/INDEX.md)

**Executor:** deepseek-v4-pro via `opencode run`
**Fallback used:** No

All artifacts complete. All tasks complete.
```

When a fallback to Sonnet occurred, replace the **Executor** / **Fallback used** lines with:

```
**Executor:** deepseek-v4-pro via `opencode run` (FAILED — <brief description of how>)
**Fallback used:** Yes — Sonnet subagent completed the work.
```

**Guardrails**
- Always prompt for change selection if not provided
- Use artifact graph (openspec status --json) for completion checking
- Don't block archive on warnings - just inform and confirm
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- If sync is requested, pass that decision to the archive-executor (it performs the sync)
- If delta specs exist, always run the sync assessment and show the combined summary before prompting
- **Reconciliation is NOT optional** — it is the load-bearing half of archive. A directory move without reconciliation leaves the next session blind. The archive-executor performs reconciliation with fresh context from the change artifacts; the primary reviews and repairs before committing. If source files are absent, the executor produces minimal entries noting the gap — the primary confirms this is acceptable before committing.
- **PHASE GATE**: Archive is the final phase. When complete, show the summary and STOP. Do not start any new workflow without an explicit user request. This is a hard rule.
