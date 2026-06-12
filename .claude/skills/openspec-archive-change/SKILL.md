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
   any incomplete task means implementation work genuinely remains (not a pending doc/spec step).

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

   If user chooses sync, use Task tool (subagent_type: "general-purpose", prompt: "Use Skill tool to invoke openspec-sync-specs for change '<name>'. Delta spec analysis: <include the analyzed delta spec summary>"). Proceed to archive regardless of choice.

5. **Perform the archive**

   Create an `archive` directory under `planningHome.changesDir` if it doesn't exist:
   ```bash
   mkdir -p "<planningHome.changesDir>/archive"
   ```

   Generate target name using current date: `YYYY-MM-DD-<change-name>`

   **Check if target already exists:**
   - If yes: Fail with error, suggest renaming existing archive or using different date
   - If no: Move `changeRoot` to the archive directory

   ```bash
   mv "<changeRoot>" "<planningHome.changesDir>/archive/YYYY-MM-DD-<name>"
   ```

6. **Reconcile project-state docs (MANDATORY — the handoff half of archive)**

   Archive is a **handoff**, not a directory move. A fresh session seeded from the change directory
   and the three project-tracked docs (`STATUS.md`, `ai-docs/decisions.md`, `ai-docs/open-questions.md`)
   must understand what shipped, why, and what follows — without any conversation transcript.
   Reconciliation writes that durable summary.

   **Source material:** Read these files from the **archived** change directory (`<archivePath>/`):
   - `notes.md` — verify verdict, concrete live output eyeballed, any defects found/fixed, as-built
     deltas, candidate follow-ons for open-questions
   - `proposal.md` — problem statement, scope, what changed
   - `design.md` — key design decisions with rationale (often labeled D1, D2, …), risks identified

   If `notes.md` lacks a verify section, extract what you can from `proposal.md` and `design.md` instead.
   If none of these files exist, note that and produce minimal entries.

   ### 6a. Reconcile `STATUS.md`

   - **Add a `## Latest change — <title> SHIPPED (<date>)` section** right after the preamble
     paragraph (before any existing `## Latest change` or `## Prior change` heading).
      Content: name the change, link the archive path, summarize what shipped (from
     proposal.md), include **concrete verify results from notes.md** — real numbers, sources, ratios,
     log lines actually eyeballed — not just "tests pass". Point to the decisions.md and
     open-questions.md sections for rationale and follow-ons. Follow the dense-paragraph style of
     existing `## Latest change` entries.
   - **Demote the previous `## Latest change`** heading to `## Prior change` (preserve its content
     exactly — do not edit or summarize it).
   - **Read `## Immediate next action`** near the file end. If this change removes a block or
     completes a pending build, update accordingly: state there is **no proactive build in flight**
     (if true) and name the next concrete step. If the change adds new gated work, mention it.

   ### 6b. Reconcile `ai-docs/decisions.md`

   - **Append** (at end of file before trailing `---` if any) a `## <title> (<date>)` section.
     Structure it as:
     - `**Decision:**` — what was built (from proposal + design).
     - `**Why now / why this shape:**` — bullet list of key design choices with rationale (from
       design.md's Decisions section). Each bullet explains *why* that choice was made and what
       alternative was rejected — including approaches investigated and rejected, with the reason,
       so they are not re-attempted. This is the durable "why" that prevents re-litigation.
     - `**Motivation:**` — the problem this solves and why it matters now (from proposal.md).
      - Include the archive path and new/modified capability spec paths.
   - **Never fabricate rationale.** If a design choice's motivation is unclear and matters enough
     to record, extract it verbatim from design.md. If it doesn't matter enough, omit it.
   - Mark superseded decisions with `~~strikethrough~~` — never delete them.

   ### 6c. Reconcile `ai-docs/open-questions.md`

   - **Append** a `## <topic> (shipped <date>)` section. Open with a one-paragraph summary of
     what shipped and where to find the full decision.
   - **Pull the open follow-ons** from notes.md's "Candidate open-questions / follow-ons for archive"
     section (if present), or from design.md's Risks / deferred Non-Goals. Each as a bullet
     describing what's open, what gates resolution, and whether it blocks other work.
   - **Flag blocking items** with **BLOCKING** where they gate other work.
   - Keep bullets lean — this file is the operator's scan list; resolved items move to
     `ai-docs/archive/retired-notes.md`.

   ### 6d. Commit the reconciliation

   After all three files are edited, **commit** with a message like:
   ```
   Reconcile project docs for <change-name> archive
   ```
    This can be a separate commit or folded into the archive commit — but it must be committed.

  **The commit hash chicken-and-egg:** The reconciliation commit produces the hash, so the hash
  cannot be known at reconciliation time. Do NOT include commit hashes in reconciled doc entries —
  reference the change by its archive path instead (the hash is one ``git log -- <archive-path>``
  away). If a prior entry says "commit pending," it is a bug from a previous archive that should
  be stamped retroactively (search and stamp the hash from ``git log -- <archive-path>``).

7. **Display summary**

   Show archive completion summary including:
   - Change name
   - Schema that was used
   - Archive location
   - Whether specs were synced (if applicable)
   - Whether project docs were reconciled
   - Note about any warnings (incomplete artifacts/tasks)

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** ✓ Synced to main specs (or "No delta specs" or "Sync skipped")
**Project docs:** ✓ Reconciled (STATUS.md, decisions.md, open-questions.md)

All artifacts complete. All tasks complete.
```

**Guardrails**
- Always prompt for change selection if not provided
- Use artifact graph (openspec status --json) for completion checking
- Don't block archive on warnings - just inform and confirm
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- If sync is requested, use openspec-sync-specs approach (agent-driven)
- If delta specs exist, always run the sync assessment and show the combined summary before prompting
- **Reconciliation is NOT optional** — it is the load-bearing half of archive. A directory move without
  reconciliation leaves a fresh session blind. If notes.md has no verify section, read proposal.md and
  design.md for source material. If all source files are absent, produce minimal entries noting the gap.
- **PHASE GATE**: Archive is the final phase. When complete, show the summary and STOP. Do not start any new workflow without an explicit user request. This is a hard rule.
