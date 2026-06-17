# Edit-Sites Dossier — openspec-scaffold golden source
**Generated:** 2026-06-13  
**Purpose:** Verbatim text at 8 edit sites (10 logical targets) for precise edit-plan authoring.  
**Scope:** READ-ONLY; no files were modified.

---

## Site 1 (T1-1) — Completion detection in apply + archive skills

### 1a. apply-change — EXIT-file sentinel (written)

**File:** `.claude/skills/openspec-apply-change/SKILL.md`  
**Lines 93–109** (the `opencode run` invocation block, showing exactly where the sentinel is appended):

```
      ```bash
      timeout -k 30 600 opencode run \
        --agent apply-executor \
        --model deepseek/deepseek-v4-flash \
        --format json \
        "Implement the OpenSpec change in <changeRoot>. Work <changeRoot>/tasks.md \
         sequentially, top to bottom, following <changeRoot>/design.md and \
         <changeRoot>/proposal.md. Check off each task ([ ] -> [x]) in tasks.md as it \
         lands. Do not modify proposal.md or design.md. Do not commit. End with a brief \
         completion report (what was implemented, deviations, what the primary should \
         check at verify, and any external-API behavior you ASSUMED rather than verified)." \
        > /tmp/apply-out.jsonl 2> /tmp/apply-err.log; \
      echo "EXIT=$?" > /tmp/apply-out.exit
      ```

      The trailing `echo "EXIT=$?" > /tmp/apply-out.exit` is the **completion
      sentinel** — it is MANDATORY (completion detection below depends on it).
```

### 1b. apply-change — Completion detection (poll loop / sentinel logic)

**File:** `.claude/skills/openspec-apply-change/SKILL.md`  
**Lines 124–144:**

```
      - **Completion detection — poll for the EXIT-file sentinel, never process
        liveness (binding).** Detect completion by `[ -f /tmp/apply-out.exit ]`
        in a bounded sleep loop (or simply wait for the harness
        background-completion notification); the `timeout` wrapper guarantees the
        sentinel appears within ~N+grace seconds. **NEVER poll with
        `until ! pgrep -f "<pattern>"`** — the pattern self-matches the poller's
        own `bash -c` command line, so the loop exits while the run is still
        going; and **never judge a run from a mid-execution jsonl snapshot** —
        deepseek-v4-flash/pro can legitimately take >5 minutes and a short jsonl
        mid-run is NORMAL. Conclude crash/timeout ONLY if the exit file shows
        nonzero (124 = timeout, 137 = SIGKILL), OR no opencode PID remains AND no
        exit file was ever written (genuine truncation). A premature retry or
        Sonnet fallback spawns CONCURRENT writers on the same working tree (this
        has left duplicate work) — which is exactly why completion must be judged
        from the sentinel, not guessed from process state. If the wrapper fires
        (exit 124/137 in the exit file), the apply **timed out** — treat it as an
        **operational crash** (step 4). For a very large change, prefer splitting
        delegation across task ranges over raising the ceiling — gate each slice with
        orchestrator-run targeted tests, and if your diff-read finds a defect in slice N,
        fold the scoped fix as the **first item of slice N+1's brief** instead of a
        separate fix run (sequential, no concurrent writers, one fewer invocation).
```

### 1c. apply-change — Completion determined from disk (primary completion signal)

**File:** `.claude/skills/openspec-apply-change/SKILL.md`  
**Lines 157–165:**

```
   3. **Determine success vs. failure** by reading back from disk (not just the report):

      - **Success** = the real agent ran AND every task in `tasks.md` is `[x]` AND
        the completion report does not declare an unresolved blocker.
      - **Operational crash** = non-zero exit (including a `timeout` kill — exit
        124, or 137 if SIGKILL was needed), empty/unparseable stdout, or the
        fallback-warning match from step 2.
      - **Non-crash failure** = real agent ran, but tasks remain `[ ]` / the report
        says it got stuck / output shows it gave up.
```

### 1d. archive-change — EXIT-file sentinel

**File:** `.claude/skills/openspec-archive-change/SKILL.md`  
**Lines 130–148** (the archive `opencode run` invocation):

```
      ```bash
      timeout -k 30 600 opencode run \
        --agent archive-executor \
        --model deepseek/deepseek-v4-pro \
        --format json \
        "Archive the OpenSpec change. changeRoot: <changeRoot>. \
         archivePath: <planningHome.changesDir>/archive/YYYY-MM-DD-<name>. \
         Delta spec sync requested: <yes/no>. \
         Project docs: STATUS.md, ai-docs/decisions.md, ai-docs/open-questions.md. \
         Move the change dir to the archive path, sync delta specs if requested, \
         and reconcile the three project docs from the archived notes.md / \
         proposal.md / design.md. Do not commit. End with a brief completion \
         report (what was moved, which specs synced, which docs reconciled, \
         anything the primary should double-check)." \
        > /tmp/archive-out.jsonl 2> /tmp/archive-err.log
      ```
```

> **COMPLICATION — archive has NO EXIT-file sentinel.** The archive invocation (lines 130–148) ends with `> /tmp/archive-out.jsonl 2> /tmp/archive-err.log` and that is all. There is no trailing `; echo "EXIT=$?" > /tmp/archive-out.exit` line and no polling/sentinel logic in the archive skill. The apply skill names its sentinel "the completion sentinel — it is MANDATORY." The archive skill does not. Any edit that adds or renames a sentinel in archive must also add the `echo "EXIT=$?"` line to the bash command.

### 1e. archive-change — Completion determined from disk

**File:** `.claude/skills/openspec-archive-change/SKILL.md`  
**Lines 170–179:**

```
   3. **Judge success from disk** (not just the report):

      - **Success** = the real agent ran AND `<archivePath>/` exists on disk AND
        STATUS.md / decisions.md / open-questions.md contain new reconciled content
        AND the report does not declare an unresolved blocker.
      - **Operational crash** = non-zero exit (including a timeout kill — exit 124,
        or 137 if SIGKILL was needed), empty/unparseable stdout, or the
        fallback-warning match.
      - **Non-crash failure** = real agent ran, but the archive dir is missing or
        docs show no new reconciled content.
```

### 1f. verify-change — EXIT-file sentinel (for delegated fix runs only)

**File:** `.claude/skills/openspec-verify-change/SKILL.md`  
**Line 24** (within the "On any defect: re-delegate" block):

```
>    - **Completion detection — EXIT-file sentinel, never process liveness (binding).** Append `; echo "EXIT=$?" > /tmp/fix-out.exit` to the wrapped command, run it with `run_in_background: true`, and detect completion by `[ -f /tmp/fix-out.exit ]` (or the harness background-completion notification). **NEVER poll with `pgrep -f "<pattern>"`** (it self-matches the poller's own command line) and **never judge a run from a mid-execution jsonl snapshot** — a slow run is NOT a crash. Conclude crash ONLY if the exit file shows nonzero/124/137, OR no opencode PID remains AND no exit file was ever written. Also note: scoped fix runs have repeatedly completed their work and still exited 1 at session teardown — judge success from disk (`git diff`, tests), not the exit code alone.
```

> Note: this sentinel is for the *fix* sub-delegation inside verify, not for verify itself (which is never delegated — see Site 4).

---

## Site 2 (T1-2 / T1-5 / T1-10) — decisions.md entire current content

**File:** `ai-docs/decisions.md`  
**Lines 1–14** (entire file):

```markdown
# Decisions

Durable architectural decisions and their rationale. Add an entry whenever a non-obvious choice is made that a future agent would otherwise re-litigate.

---

<!-- Format:
## Decision: <short title>
**Date:** YYYY-MM-DD
**Decision:** What was decided.
**Rationale:** Why.
**Alternatives considered:** What was rejected and why.
-->
```

> **Notes on format:** The file is empty of real entries — only the header and a commented-out format block. The entry format is defined inside `<!-- ... -->` comments (H2 heading `## Decision: <short title>`, then three bold-label fields: `**Date:**`, `**Decision:**`, `**Rationale:**`, `**Alternatives considered:**`). Seeded entries must match this format exactly and be placed after the `---` separator, outside the comment block.

---

## Site 3 (T1-3) — Spec scenario format (EARS / WHEN-THEN-AND)

### 3a. propose skill — the authoritative template

**File:** `.claude/skills/openspec-propose/SKILL.md`  
**Lines 279–298** (spec draft shown to user during Specs phase):

```
```
Here's the spec:

---

## ADDED Requirements

### Requirement: <Name>

<Description of what the system should do>

#### Scenario: <Scenario name>

- **WHEN** <trigger condition>
- **THEN** <expected outcome>
- **AND** <additional outcome if needed>

---

This format—WHEN/THEN/AND—makes requirements testable. You can literally read them as test cases.
```
```

### 3b. onboard skill — same template with narration

**File:** `.claude/skills/openspec-onboard/SKILL.md`  
**Lines 277–298:**

```
**DO:** Resolve where the spec file should be created:
```bash
openspec instructions specs --change "<name>" --json
# Use resolvedOutputPath from the JSON. If it is a glob, choose the concrete file path using the schema instruction and workspace planning context.
```

Draft the spec content:

```
Here's the spec:

---

## ADDED Requirements

### Requirement: <Name>

<Description of what the system should do>

#### Scenario: <Scenario name>

- **WHEN** <trigger condition>
- **THEN** <expected outcome>
- **AND** <additional outcome if needed>

---

This format—WHEN/THEN/AND—makes requirements testable. You can literally read them as test cases.
```

Save to the concrete file path chosen from `resolvedOutputPath`.
```

### 3c. verify skill — scenario marker used for coverage checking

**File:** `.claude/skills/openspec-verify-change/SKILL.md`  
**Lines 111–117:**

```
   **Scenario Coverage**:
   - For each scenario in delta specs (marked with "#### Scenario:"):
     - Check if conditions are handled in code
     - Check if tests exist covering the scenario
     - If scenario appears uncovered:
       - Add WARNING: "Scenario not covered: <scenario name>"
       - Recommendation: "Add test or implementation for scenario: <description>"
```

> **Confirmation:** The scaffold uses a literal `WHEN/THEN/AND` event-driven format. The exact markers are `#### Scenario:` (H4 heading), `- **WHEN**`, `- **THEN**`, `- **AND**`. This format is defined identically in both the propose skill and the onboard skill. It is NOT in `openspec/config.yaml` or `AGENTS.md`. The verify skill uses `"#### Scenario:"` as the machine-readable marker for coverage checking.

---

## Site 4 (T1-4) — Why verify isn't delegated

**File:** `.claude/skills/openspec-verify-change/SKILL.md`  
**Lines 14–30** (the MANDATORY block header and body):

```
> **MANDATORY — behavioral review. This is the core of verify, not optional, and runs BEFORE the artifact/spec checklist below.**
> Per `AGENTS.md` and `openspec/config.yaml`, verifying a change is the orchestrator's own review of the apply-executor's work — a substantive behavioral review, not a checklist rubber-stamp. Before generating the verification report, the main agent MUST itself do all of the following — do not delegate this, and do not trust the executor's completion summary:
>
> 1. **Read the actual diffs and changed files.** Run `git diff` (and open the files) for everything the executor touched. Trust the code, not the summary.
> 2. **Re-run the FULL test suite yourself:** `.venv/bin/python -m pytest -q`. It must be green (pre-existing skips OK). A green exit is **necessary but not sufficient.**
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
```

> **COMPLICATION — `@openspec-reviewer` does NOT appear in verify-change/SKILL.md at all.** The `@openspec-reviewer` (deepseek-v4-pro read-only auditor) is defined in AGENTS.md lines 63–66 and invoked during the *propose* skill — not verify. The verify skill calls the pattern "do not delegate this" (line 15) and re-delegates *fixes* (not the verification itself) to a "FRESH apply-executor" (lines 21–28). If you want to name the "separate-verifier / adversarial-agent" pattern, the anchor for that is the proposal-phase reviewer in AGENTS.md lines 63–66 (quoted in Site 7 below) plus the verify skill's own "do not delegate" framing above.

---

## Site 5 (T1-6) — Fold-fix guidance

### 5a. apply-change — fold-fix text

**File:** `.claude/skills/openspec-apply-change/SKILL.md`  
**Lines 140–144** (end of the completion-detection block):

```
        For a very large change, prefer splitting
        delegation across task ranges over raising the ceiling — gate each slice with
        orchestrator-run targeted tests, and if your diff-read finds a defect in slice N,
        fold the scoped fix as the **first item of slice N+1's brief** instead of a
        separate fix run (sequential, no concurrent writers, one fewer invocation).
```

### 5b. AGENTS.md — cross-cutting headings (anchor for a promoted fold-fix rule)

**File:** `AGENTS.md`  
The file has these top-level `##` sections in order:

| Line | Heading |
|------|---------|
| 24   | `## Cross-agent compatibility (load-bearing — do not weaken)` |
| 36   | `## Project context` |
| 50   | `## Roles` |
| 69   | `## OpenSpec workflow` |
| 92   | `## State, write discipline, and the archive-as-handoff rule` |
| 112  | `## Working process` |
| 162  | `## Web research convention` |
| 171  | `## After reading this file` |

> There is no heading called "Rules" in AGENTS.md. A promoted general fold-fix rule would most naturally attach to **`## Working process`** (lines 112–161), which already contains all the per-task behavioral guidance (scripts, resumability, subagent use, tests, commits). Alternatively it could open or close the `## OpenSpec workflow` section (lines 69–91). Either is editorially valid; `## Working process` is the more direct fit because the fold-fix rule governs how the executor delegation loop behaves across slices.

---

## Site 6 (T1-7) — When NOT to delegate (delegation policy)

**File:** `AGENTS.md`  
**Lines 126–129** (the "Use subagents for independent work" bullet inside `## Working process`):

```
- **Use subagents for independent work.** Parallelize independent research/extraction
  across subagents freely; prefer a cheaper model (e.g. Sonnet) for extraction. Always
  apply your own judgment to their reports — they have been wrong before — and have each
  subagent checkpoint findings to disk so the work survives interruption.
```

> This is the only delegation-policy text in AGENTS.md. It encourages parallelism but contains no guardrail about dependency-laden work. The sentence "Parallelize independent research/extraction across subagents freely" is the precise anchor for adding a caveat: delegation only helps when tasks are genuinely independent; dependency-chained work degrades under fan-out.

---

## Site 7 (T1-8) — "Constitution" (onboard + hard-constraints block)

### 7a. openspec-onboard/SKILL.md — agent orientation passage

**File:** `.claude/skills/openspec-onboard/SKILL.md`

> **COMPLICATION — the onboard skill has NO passage walking a new agent through AGENTS.md or hard-constraints.** The onboard skill is a *user-facing tutorial*: it teaches a human user the workflow by doing a real task. Its description says "Guide the user through their first complete OpenSpec workflow cycle." It has no step that reads AGENTS.md, no acknowledgment of hard-constraints, and no constitution framing. If you intend to name a constitution passage and anchor it to the onboard skill, that passage does not yet exist and would need to be added.
>
> The closest passage in the onboard skill is Phase 5–6 which explains what proposals and specs are — structural context for users, not agent constraints.

### 7b. AGENTS.md — hard-constraints block header and intro

**File:** `AGENTS.md`  
**Lines 1–22** (the MANDATORY preamble block — the de facto agent-orientation "constitution"):

```
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
```

**Lines 24–34** (the "Cross-agent compatibility" section immediately following, labeled "load-bearing — do not weaken"):

```
## Cross-agent compatibility (load-bearing — do not weaken)

This repo is worked by **both Claude and non-Claude agents** (OpenCode/DeepSeek).
For that to work, **all project state lives in tracked, agent-neutral files** — never in
harness-private storage. Concretely, do **not** read from, write to, or rely on:
- Global or cross-session memory, harness memory, or any assistant-specific config
  files/directories (`.claude/`, `CLAUDE.md`, memory files, etc.) — record project
  knowledge in `ai-docs/` and the OpenSpec artifacts instead.
- External repos or documentation you were not explicitly pointed to.

Maintain this discipline for the **entire session**, not just at the start.
```

**Lines 47–48** (the "Hard constraints" field in `## Project context`):

```
**Hard constraints:** <FILL: API tiers, cost limits, platform/runtime constraints,
anything the agent must never violate — or remove this section if none.>
```

> **Note:** The "Hard constraints" block is currently a placeholder `<FILL:...>` — it has never been filled in for this scaffold template. The section that most functions as a project "constitution" is the MANDATORY preamble (lines 1–22) plus the "Cross-agent compatibility" block (lines 24–34). Naming that compound as the "constitution" is editorially sound and maps to real text. The `## After reading this file` block (lines 171–179) is the acknowledgment checklist that closes orientation.

**Lines 171–179** (the acknowledgment checklist):

```
## After reading this file
Acknowledge four things before acting: (1) your role as orchestrator/reviewer who runs
the OpenSpec lifecycle and does not implement; (2) that apply is delegated to a
sequential apply-executor and verify is *your* deep behavioral review; (3) that when
verify finds a bug you diagnose and scope it, then re-delegate the fix to a fresh
executor (deepseek-first, Sonnet-fallback — see verify skill for the ladder; only
trivial typo-level changes inline); (4) that you write the change dir
continuously but reconcile `STATUS.md`/`ai-docs/` only at archive, by delegating
to the archive-executor (deepseek-v4-pro), then reviewing and committing.
```

---

## Site 8 (T1-9) — Skill-tool wording

**File:** `AGENTS.md`  
**Lines 80–83** (verbatim):

```
**Phase-specific procedural rules live in the skill files, not here.**
The agent invokes the appropriate skill (via the Skill tool) when a phase is entered.
AGENTS.md carries only cross-cutting rules that span multiple phases.
Skill files: `.claude/skills/openspec-*-change/SKILL.md`.
```

> This is a four-line block. "via the Skill tool" is the harness-specific phrase you want to reword. The surrounding context names the files at `.claude/skills/openspec-*-change/SKILL.md` — note this path pattern excludes `openspec-onboard` and `openspec-explore` (no `-change/` suffix), so the glob as written is slightly narrower than all skills. A harness-neutral reword might say "by invoking the appropriate skill" or "using the platform's skill-invocation mechanism" instead of naming the Skill tool. Adjust the file-path glob if the intent is to cover all `.claude/skills/openspec-*/SKILL.md` files.

---

## Summary of surprises / complications

| Site | Complication |
|------|-------------|
| T1-1 (archive) | The archive skill's `opencode run` invocation has **no** `echo "EXIT=$?" > /tmp/archive-out.exit` sentinel. Apply has it; archive does not. Any rename of "sentinel" in archive must also ADD the sentinel line to the bash block. |
| T1-4 (verify) | `@openspec-reviewer` is **not mentioned** in `openspec-verify-change/SKILL.md`. It lives in AGENTS.md lines 63–66 and is invoked from the propose skill. The "separate-verifier / adversarial-agent" concept must be named against the propose+AGENTS.md context, not the verify skill. |
| T1-8 (constitution / onboard) | `openspec-onboard/SKILL.md` contains **no passage walking an agent through AGENTS.md or hard-constraints**. It is a user tutorial. If you want an agent-orientation "read AGENTS.md first" step in onboard, it must be added. The "constitution" label maps most cleanly to AGENTS.md lines 1–34. |
| T1-9 (skill-tool) | The file-glob `openspec-*-change/SKILL.md` (line 83) excludes `openspec-explore` and `openspec-onboard` — those are `openspec-explore/SKILL.md` and `openspec-onboard/SKILL.md` without the `-change` suffix. A reword that also broadens the glob to `openspec-*/SKILL.md` may be warranted. |
| T1-3 (EARS) | The WHEN/THEN/AND template appears in two places (propose + onboard skills) but NOT in `config.yaml` or `AGENTS.md`. The authoritative definition is in the propose skill. |
| T1-6 (fold-fix in AGENTS.md) | AGENTS.md has no "Rules" section heading. The nearest home for a promoted fold-fix rule is `## Working process`. |
