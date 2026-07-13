# Recon — OW-10 (apply-executor throughput + resume contract)

Read-only reconnaissance, current working-tree state (includes uncommitted OW-7 delegation-wrapper
changes — confirmed present as unstaged diffs to 6 files + untracked
`openspec/changes/delegation-wrapper-telemetry/` with ALL tasks `[x]` but not yet archived).
No source was edited to produce this file.

Design source: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md` finding 4 (lines 107-115),
restated in `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md:207-212` and
`knowledge/HANDOFF.md:41-45`.

---

## 1. `.claude/skills/openspec-apply-change/SKILL.md` — full current structure (post-OW-7)

File is 337 lines. Structure: frontmatter (1-10) → delegation-override banner (14-19) → phase-gate
banner (21) → Steps 1-7 (25-257) → Output templates (258-317) → Guardrails (319-329) → Fluid
workflow note (331-337).

### 1a. Test-cadence wording — does it say "full suite after every task"?

**Not in this file at all.** `SKILL.md` never mentions running tests directly — it only orchestrates
the delegation call and post-hoc triage. The test-cadence instruction lives entirely in the
**executor agent bodies** (`.claude/agents/apply-executor.md` / `.opencode/agents/apply-executor.md`,
byte-identical, see §2), specifically their **Step 2** of the per-task loop:

> `.claude/agents/apply-executor.md:23-29` (identical in `.opencode/agents/apply-executor.md:33-39`):
> ```
> 2. **Run the project's tests** using the per-repo test command:
>    - Prefer `scripts/test-cmd` (one-line file in the repo root).
>    - If `scripts/test-cmd` is absent, use the project's standard/documented test
>      command (e.g. check `pyproject.toml` for pytest config, `Makefile` for a
>      `test` target, or `package.json` for a `test` script).
>    - **Never improvise** an ad-hoc `pytest` or other command that may pick the
>      wrong venv/flags.
> ```
> This project's own `scripts/test-cmd` = `pytest -q` (no path arg — i.e. the **full suite**, verified
> by reading the file directly). This step runs **unconditionally, once per task**, before the
> green/red branch (step 3/4) — so today every task-completion pays a full-suite run. This is the
> literal mechanism behind the audit's "full suite after every task" claim; there is no separate
> "targeted" invocation anywhere in the green path.

**Targeted-vs-full wording** appears in exactly one place, and only inside the **red-path retry
loop**, not as an alternative to step 2's initial run:

> `.claude/agents/apply-executor.md:43-46` (step 4, `CONTINUE` bullet):
> ```
> - **`CONTINUE`** → fix the code based on the failure, then **return to
>   step 2** (do NOT advance to the next task — CONTINUE means keep working
>   this failure; re-run only the failing test's module if practical, not
>   necessarily the whole suite).
> ```
> So: the FIRST test run per task is always full (`scripts/test-cmd`); only *subsequent* fix-retry
> iterations *within* an already-red task are allowed to narrow to the failing module. There is no
> "run targeted, then full once per slice" concept anywhere today.

**Red-path helper** (`scripts/_convergence.py`, invoked at step 4) takes the raw output of that same
test-cmd run on stdin and returns `CONTINUE` / `STOP:<a|b|c>:<detail>` — it does not itself run
tests; it is a stateful classifier over output already produced by step 2's full-suite run (durable
per-change state in `/tmp/apply-convergence-<slug>.json`, `_MAX_ATTEMPTS = 20` backstop — confirmed
by reading `scripts/_convergence.py:1-33`).

### 1b. The "slice" concept — how bounded/triggered today; 600s relation

Slicing is mentioned **only in `SKILL.md`**, inside Step 6's "Invoke the executor" caveats (not in
the executor agent bodies, which have no concept of slices — an executor invocation just works
straight through `tasks.md` until done or blocked):

> `.claude/skills/openspec-apply-change/SKILL.md:128-145`:
> ```
> **Bounded wait + EXIT-sentinel (§c–d):** Run this Bash call with
> `run_in_background: true`; detect completion via `[ -f /tmp/apply-out.exit ]`.
> A premature retry or Sonnet fallback spawns CONCURRENT writers on the same
> working tree (this has left duplicate work) — which is exactly why completion
> must be judged from the sentinel, not guessed from process state. If the wrapper
> fires (exit 124/137 in the exit file), the apply **timed out** — treat it as an
> **operational crash** (see Failure modes). For a very large change, prefer splitting
> delegation across task ranges over raising the ceiling. **Why split:** the executor's
> hard timeout budget (~600s) is the ceiling on any single invocation — splitting keeps
> each run within budget, not to create intermediate review checkpoints. Between slices
> the primary reads `git diff` and runs targeted tests as a smoke (crash/blocker
> detection only, not a behavioral review); the real behavioral review happens at verify.
> If your diff-read finds a defect in slice N, fold the scoped fix as the **first item
> of slice N+1's brief** instead of a separate fix run (sequential, no concurrent
> writers, one fewer invocation).
> ```

Key facts:
- A "slice" = an arbitrary **task-range subset** of `tasks.md` the orchestrator manually carves out
  ("splitting delegation across task ranges") for one `opencode run` invocation.
- **No numeric or structural trigger is defined** — no task-count threshold, no estimated-duration
  heuristic. The only stated trigger is judgment: "for a **very large** change, prefer splitting."
  There is no criterion in the skill for *when* a change counts as "very large" — this is left
  entirely to orchestrator discretion.
- The **~600s budget IS explicitly the reason slicing exists** ("the executor's hard timeout budget
  (~600s) is the ceiling on any single invocation — splitting keeps each run within budget"). This is
  the single sentence AUDIT.md finding 4 is targeting when it says "the 600s ceiling binds."
- Between slices the primary does a **git-diff read + targeted-test smoke** (crash/blocker detection
  only, explicitly NOT a behavioral review — that's deferred to verify) — this is the ONLY place
  "targeted tests" already exists in the apply flow, and it's an orchestrator-side smoke between
  slices, not something the executor itself does per-task.
- This whole slicing paragraph is annotated with a delegation cue (line 143-145) citing
  `delegation-by-default`: the between-slice git-diff-read + targeted-test smoke is itself flagged as
  delegable to a haiku/Sonnet subagent (not yet mechanized — this is a candidate collision surface if
  OW-10 also touches this same paragraph, see §1e).

### 1c. Retry / fresh-executor / re-brief section — current wording, and the gap

This is the **Failure ladder**, `SKILL.md:199-222`, item 1 (the retry branch):

> ```
> 3. **Failure ladder:**
>
>    - **Operational crash** → **retry the `opencode run` once** (if it timed out,
>      retry with a **tight brief**: name the exact files to read, front-load the facts
>      you've already verified as given, and forbid codebase re-exploration — the wrapper
>      is a hard ceiling and the executor otherwise burns its budget re-deriving context
>      you already have). Second crash → spawn a **Sonnet subagent**
>      apply-executor (`Agent` tool, `subagent_type: "apply-executor"`) to finish
>      `tasks.md`.
> ```

This is the **exact re-brief guidance** that exists today. It already gestures at the "burns its
budget re-deriving context" lesson (word-for-word close to the extrends lesson quoted in the OW-10
brief) as the rationale for a "tight brief," but:

- It says "name the exact files to read, front-load the facts you've already verified as given, and
  forbid codebase re-exploration" — this is **prose guidance to the orchestrator about brief-writing
  discipline**, not a structured "resume contract."
- **It does NOT say**: skip `[x]` tasks, resume at the first `[ ]` task, or reconcile the half-edited
  in-flight task (the task that was mid-edit when the prior executor died). None of those three
  phrases or their concepts appear anywhere in this ladder, nor in the "declared blocker" triage
  branches immediately below it (lines 208-215, which cover *fresh executor* dispatch for a
  brief/plan gap, but again with no resume-contract language), nor in the OpenCode-path failure
  handling (lines 224-247, same absence — "dispatch a **fresh** `@apply-executor`" with zero
  resume-state instructions).
- **Confirmed gap**, exactly as the OW-10 brief anticipated: there is no text anywhere in this file
  instructing the orchestrator to (a) tell the fresh executor which tasks are already `[x]` and to
  skip them, (b) tell it to resume at the first `[ ]`, or (c) specifically re-examine/reconcile the
  task that was mid-edit when the prior run died (as opposed to just "resume `tasks.md`" generically).
  The retry-brief instruction only says what to avoid (re-exploration) and what to front-load
  ("facts you've already verified"), not the structural resume mechanics.

### 1d. Existing "resume contract" / "distilled state" / "carry-forward" language

**None exists in the skill, the agent bodies, or the harness doc.** Repo-wide grep for
`distilled state`, `distilled-state`, `carry-forward` (workflow sense), `resume contract`,
`resume-contract`, `no subagent resume`, `deepseek burns most of its budget`, and `extrends lesson`
turns up hits **only** in the planning/audit documents that already justify OW-10 itself:
- `knowledge/research/workflow-audit-2026-07-11/AUDIT.md:107-115` (finding 4 — the design brief)
- `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md:207-212` (OW-10 backlog entry)
- `knowledge/HANDOFF.md:41-45` (OW-10 handoff summary)
- `knowledge/roadmap.md:43` (one-line roadmap pointer)
- `knowledge/research/workflow-audit-2026-07-11/friction-evidence.md:328` and
  `extrends-friction.md:85` (the sourced extrends lesson quote, evidentiary, not normative)
- `AGENTS.md:310` and `knowledge/research/workflow-harmonization-plan-2026-06.md:336` — these carry
  the **generic** "no subagent resume" principle (see §4) but not an apply-specific resume contract.

Confirmed: **the resume contract does not exist anywhere in shipped instruction surfaces today** —
OW-10 would be introducing genuinely new prose, not editing/correcting an existing (wrong) version.

### 1e. Where OW-7's wrapper touched the failure-modes section (collision map for OW-10)

OW-7 (uncommitted, all tasks `[x]`) rewrote `SKILL.md`'s Failure-modes **item 1** (assert-ran +
extract) to call the new `scripts/opencode_delegate.py` wrapper. Current (post-OW-7) text,
`SKILL.md:155-197`:

```
1. **Assert the real executor ran (§b) + extract completion text via wrapper:**
   Invoke `scripts/opencode_delegate.py` for post-processing, ...
   scripts/opencode_delegate.py \
     --phase apply --agent apply-executor --model deepseek/deepseek-v4-flash --change <name> \
     --out /tmp/apply-out.jsonl --err /tmp/apply-err.log \
     --exit-file /tmp/apply-out.exit \
     --quiet
   ...
   Read the extracted text from `/tmp/apply-out.jsonl.text.txt` ...
```//
(item 2, "Determine success vs. failure," lines 170-197, and the
`### NON-CONVERGENCE BLOCKER` grep, are also OW-7-touched — they now read from
`/tmp/apply-out.jsonl.text.txt` instead of re-parsing raw jsonl.)

**Collision assessment for OW-10:**
- OW-10's natural edit targets are (i) Step 6.1's slicing paragraph (`SKILL.md:128-145`, §1b above)
  for the targeted-vs-full cadence description, and (ii) Failure-ladder **item 1** of the ladder
  (`SKILL.md:199-207`, §1c above) for the resume contract — **not** the OW-7-touched assert-ran/
  extract block (items 1-2 of the *triage* numbering at 155-197, a different numbered list than the
  *ladder's* item 1 at 199+). These are two different "item 1"s in the same **Failure modes**
  section — easy to conflate when citing line numbers in a future tasks.md; the recon here
  distinguishes them explicitly: "wrapper-invocation item 1" (155-168) vs. "failure-ladder item 1"
  (199-207).
- No literal overlap in lines needing to change, but OW-10 should NOT touch the wrapper invocation
  block (155-168) or its `/tmp/apply-out.jsonl.text.txt` read pattern — that's OW-7's surface and is
  functioning/tested. OW-10 only needs to add resume-contract prose to the ladder's retry bullet
  (199-207) and possibly a new "brief template" subsection near it.
- Numbering caveat: `SKILL.md`'s Failure-modes triage list uses `1.`/`2.` (with 4-space indent,
  rendering oddly — see raw line 155 `    1.` vs line 170 `   2.`), then a separate `3. **Failure
  ladder:**` at the same nesting as the outer numbered steps. Any OW-10 edit should re-read exact
  current line numbers before writing tasks.md anchors, since this file will have shifted once OW-7's
  diff (currently unstaged) is committed — **line numbers in this recon are from the current
  working-tree file, matching what OW-10 will actually branch from**, so they're safe to cite as long
  as OW-7 lands first (per the HANDOFF.md recommended order: OW-7 → OW-10).

---

## 2. Executor agent definitions — `.claude/agents/apply-executor.md` and `.opencode/agents/apply-executor.md`

Both files are **98/97-line bodies** (`.claude` has 88 lines total + 10-line frontmatter = 98;
`.opencode` has 97 lines total + frontmatter). Confirmed **byte-identical apart from one sanctioned
clause**: the `.claude` intro sentence at line 8 reads "You are the apply executor for OpenSpec
changes (the Claude Code counterpart of the OpenCode `@apply-executor`)." while `.opencode` line 19
reads "You are the apply executor for OpenSpec changes." (no parenthetical) — every other line,
including all step numbering, the Non-Convergence Blocker format block, and the Rules section, is
character-for-character the same.

**Cadence/slice/resume content in the agent bodies themselves:**
- **Test cadence:** yes — step 2 (quoted in §1a) is the *only* place the full-suite-per-task rule is
  actually specified; the skill file merely delegates to it.
- **Slices:** **no mention at all.** The executor has no concept of a slice — it just works
  `tasks.md` top-to-bottom until done, blocked, or (implicitly) killed by the orchestrator's external
  `timeout` wrapper. Slicing is purely an orchestrator-side invocation-splitting concern (§1b);
  nothing inside the executor's own instructions changes behavior based on being given a partial
  task range.
- **Resume:** **no mention at all.** There is no "if some tasks are already `[x]`, skip them" or
  "if you're given a partial brief, treat it as continuing from where a prior run stopped" language.
  The executor's only self-referential state is the `_convergence.py` per-change JSON file
  (red-path only, keyed by `--change` + `--task`), which is NOT a general resume/checkpoint
  mechanism — it only tracks fix-attempt counts and file-touch counts for the currently-failing test,
  and is silent about which tasks are done or what "resuming" means structurally.

**Sync constraint — `scripts/test_executor_body_agreement.py` (confirmed by reading the script,
`scripts/test_executor_body_agreement.py:1-126`):**
- It compares **the two agent files' bodies only** (frontmatter stripped by
  `read_and_strip_frontmatter`, splitting on the leading/closing `---` YAML delimiters) — **not the
  whole file**, so `model:`/`tools:`/`permission:` frontmatter differences between the two platforms
  are explicitly out of scope for this test and can differ freely.
- After stripping frontmatter, it applies exactly one normalization
  (`_INTRO_CLAUSE_RE` regex, stripping `"(the Claude Code counterpart of the OpenCode `@<role>`)"` from
  the `.claude` body) and then asserts the **remainder is byte-identical** (`assertEqual` on full
  strings, not a line diff or semantic comparison).
- **Implication for OW-10:** if OW-10 changes the apply-executor's test-cadence instruction (step 2)
  or adds resume-awareness prose to the agent body itself (as opposed to only the orchestrator-side
  `SKILL.md`), **both** `.claude/agents/apply-executor.md` and `.opencode/agents/apply-executor.md`
  must receive the identical edit (save for the one sanctioned intro clause), or this test fails.
  There are two independent copies of the executor's own instructions to keep in sync — this is a
  real, mechanically-enforced constraint, not just documentation-hygiene advice. If OW-10's design
  keeps the resume contract entirely in the orchestrator-side `SKILL.md` (which drives the *brief*
  given to a fresh executor invocation) and does not change the executor's own step-by-step
  instructions, this sync constraint is **not triggered** — the agent bodies would stay unchanged.
  This is the cheaper design option and worth calling out explicitly in OW-10's design.md.

---

## 3. `openspec/specs/apply-convergence-guard/spec.md` — does it need a delta?

Full spec quoted for context (161 lines). Its **Purpose**: "Stop the apply-executor from looping on a
stuck failure by giving it an objective, deterministic non-convergence stop condition, and route a
diagnosed blocker to orchestrator triage instead of reflexive escalation." Five requirements:
1. **"The apply-executor stops on non-convergence"** (lines 7-53) — defines rules (a)/(b)/(c) and
   states: *"For its test runs the executor SHALL prefer the same per-repo test command as the
   commit-test-gate (`scripts/test-cmd`), falling back to the project's standard/documented test
   command when `scripts/test-cmd` is absent — never an improvised command."* (lines 13-15)
2. **"Non-convergence detection is deterministic, not in-context judgment"** (55-103) — the
   `_convergence.py` helper contract (normalization, git-diff-derived edited-file tracking, etc.).
3. **"A declared blocker is machine-discriminable from an opaque give-up"** (104-121) — the
   `### NON-CONVERGENCE BLOCKER` block format.
4. **"Recovery from a declared blocker is the orchestrator's decision"** (123-143) — triage-not-
   reflexive-Sonnet routing; **explicitly covers the autonomy-mode interaction** ("an autonomy grant
   relaxes interactive checkpointing but SHALL NOT replace declared-blocker triage with an
   unconditional... ladder"), but says nothing about resume state.
5. **"The convergence guard ships with a hardened, instruction-gated canary"** (145-161) — the
   fixture/test-harness guarantee for the guard itself.

**Does OW-10 touch what this spec guarantees?**
- **Test-cadence change** genuinely brushes Requirement 1's SHALL clause (lines 13-15, quoted above).
  That sentence governs *which command* to invoke (never improvise; use `scripts/test-cmd` or the
  documented equivalent) — it does not currently speak to *scope* (whole-suite vs. targeted subset).
  If OW-10's "targeted tests per task" means invoking the *same* test tool with a narrowed target
  (e.g. `pytest -q path/to/test_file.py` instead of bare `pytest -q`), that is arguably still
  "the same per-repo test command" in spirit (same tool/venv/flags, not an improvised different
  command) but is a literal deviation from "the same... command" if read strictly, since the
  documented `scripts/test-cmd` is `pytest -q` with no path argument (verified: the file's content is
  exactly `pytest -q`). This is a genuine ambiguity worth resolving explicitly in OW-10's design.md
  and very likely warrants a **MODIFIED delta** to Requirement 1 — adding an explicit scenario or
  amending the SHALL to distinguish "same underlying command/tool, scoped by target" from "an
  improvised command" (the two are different failure modes the original wording was trying to guard
  against only the latter — wrong venv/flags — not scope narrowing).
- Requirement 2 (the `_convergence.py` contract) is **unaffected in its mechanics**: the helper
  already extracts only the failing test's section before normalizing (scenario at spec.md:71-76) and
  derives edited-files from `git diff`, independent of whether the upstream test run was full or
  targeted — but OW-10's design should note the coverage tradeoff explicitly (a full-suite run once
  per slice, not per task, means a regression in an untouched-this-task module surfaces only at
  slice-end, not immediately) — this is a design/tasks.md narrative point, not necessarily a spec
  change, since the spec's guarantee is about *detecting non-convergence in the test that's being
  run*, not about which tests get run when.
- Requirements 3, 4, 5 (blocker format, triage routing, canary) are **untouched** by cadence or resume
  changes — they govern the red-path stop/report/triage protocol, which OW-10 does not alter.
- **The resume-contract half of OW-10 is skill-prose-only, not spec-governed**: nothing in
  `apply-convergence-guard` claims anything about what a *fresh* executor invocation should be told
  about prior progress — that's purely the orchestrator's re-brief content (`SKILL.md`'s failure
  ladder), outside this spec's Purpose statement ("stop... on non-convergence... route a diagnosed
  blocker to orchestrator triage") which is scoped to the red/blocker path, not the retry-brief
  content on the operational-crash path. **No delta needed for the resume-contract half.**

**Conclusion:** OW-10 most likely needs **one small MODIFIED delta** to
`apply-convergence-guard`'s Requirement 1 (to reconcile "targeted tests per task" with the existing
"prefer the same per-repo test command... never an improvised command" SHALL) — not a new capability
and not zero-spec-impact. The resume-contract portion is skill-prose-only (no spec touches it). This
should be flagged as a design decision for OW-10's own design.md/proposal — the recon surfaces the
tension but does not resolve it (that's implementation-time judgment, out of scope for a read-only
recon).

---

## 4. The "no subagent resume" fact — where documented

Canonical location: **`AGENTS.md:310-315`** ("Working process" section):

> ```
> - **Make work resumable.** This harness has **no subagent resume**; a killed agent
>   restarts cold. Push deterministic heavy-lifting into re-runnable scripts that dump
>   intermediate results to disk; checkpoint partial findings as each section completes;
>   decompose long jobs into steps that each complete and return. Granularity buys
>   resumability. Long-running batches must be resumable from a checkpoint and **stop on
>   first failure** rather than continuing with partial state.
> ```

This is a **generic, cross-cutting principle** (not apply-specific) — it is the premise OW-10 cites,
but it does not itself describe the apply-executor's resume mechanics; it only establishes *why* a
fresh executor invocation starts cold (no memory of the dead run) and therefore *why* the orchestrator
must supply everything it needs via the brief. The same sentence is echoed verbatim in
`knowledge/research/workflow-harmonization-plan-2026-06.md:336` (a historical planning doc, not a
second normative source) and is cited/discussed (not re-stated) in
`knowledge/research/research-industry-standards-2026-06/B-orchestration-delegation.md:330` (an open
question, OQ-2, about EXIT-file sentinel adequacy under SIGKILL) and
`knowledge/research/workflow-audit-2026-07-11/lifecycle-critique.md:154`. **`AGENTS.md:310` is the
single authoritative source**; nothing in the apply skill or executor agent files restates or extends
it today (confirmed by grep — the apply-related files never use the phrase "no subagent resume" or
any close paraphrase).

---

## 5. Half-finished-run detection today — checkpoint/partial-state mechanism

**There is no dedicated checkpoint or partial-state file for apply.** The only state the orchestrator
can read back after a crash/timeout is:
- **`tasks.md`'s checkbox state** (`[x]` vs `[ ]`) — the sole progress record, read via `git diff` /
  re-reading the file (`SKILL.md:147-149`, Step 6.2: *"After the executor (deepseek or Sonnet)
  finishes, read `tasks.md` and `git diff` to confirm all tasks are checked off and changes are on
  disk."*).
- **Working-tree diff** (`git diff`) — whatever files the dead executor edited before dying, including
  a possibly half-applied edit to whatever task was in-flight. There is no separate marker
  distinguishing "this task's edit is complete but not yet tested" from "this task's edit is
  mid-write" — the orchestrator has to infer it from reading the diff and the task list together.
- **`_convergence.py`'s per-change JSON state** (`/tmp/apply-convergence-<slug>.json`) — but this is
  scoped to the red-path fix-attempt/file-touch counters for convergence detection, not a general
  "what did the executor last do" checkpoint, and it lives in `/tmp` (not durable/tracked — it would
  not survive a machine reboot and is irrelevant across a *different* invocation's process unless the
  same `--change` slug is reused, which it is by convention).
- **No `notes.md` or `review-log.md` write from the executor itself** — the apply-executor agent body
  never mentions writing to `notes.md`; that file is the orchestrator's own scratch log per AGENTS.md
  ("Change-local scratch — write continuously, in-context... During a change, freely write its
  `openspec/changes/<name>/` files... append decisions/rejected approaches/discoveries to `notes.md`"
  — `AGENTS.md:260-264`), and there is no established convention today for the *executor* to leave a
  breadcrumb there before dying (it can't — a crash by definition means it didn't get to write a
  final report).

**How the skill tells the orchestrator to detect a half-finished run:** it doesn't, explicitly, beyond
"read `tasks.md`" — Step 6.2 (`SKILL.md:147-149`) and the Failure-ladder's "Determine success vs.
failure" step (`SKILL.md:170-176`, quoted in §1a) define success as "every task in `tasks.md` is
`[x]`," implying a half-finished run is detected simply as "not all `[x]`" — there's no explicit
"identify the boundary task, distinguish complete-and-tested from mid-edit" instruction. **This
confirms the OW-10 premise directly**: today, "resume" is not a designed mechanism at all — it's an
emergent side-effect of tasks.md's checkbox state plus whatever the fresh executor happens to notice
when re-reading the file on its own initiative (nothing tells it to do so explicitly, or to treat the
first `[ ]` specially, or to double check the task immediately preceding it for a half-applied edit).

---

## Summary of surprises / things the OW-10 tasks.md author should know

1. **The two "item 1"s.** The Failure-modes section has an item-1 for wrapper post-processing
   (OW-7's territory, `SKILL.md:155-168`) and a *separate* item-1 inside the numbered "Failure
   ladder" (`SKILL.md:199-207`, the actual retry/resume-contract target) — easy to conflate when
   writing task anchors; distinguish them by content, not just "item 1."
2. **Executor-body sync is mechanically enforced** (`test_executor_body_agreement.py`, body-only,
   byte-identical after one sanctioned intro-clause strip) — if OW-10 keeps the resume contract
   purely in `SKILL.md` prose (the orchestrator's re-brief instructions) rather than the executor's
   own step-by-step instructions, this constraint is never triggered. Recommend that as the default
   design unless there's a specific reason the executor itself needs new self-knowledge.
3. **`apply-convergence-guard`'s Requirement 1 SHALL clause plausibly needs a MODIFIED delta** — its
   "prefer the same per-repo test command... never an improvised command" language was written to
   ban wrong-venv ad-hoc commands, not to ban scope-narrowing, but a strict reading collides with
   "targeted tests per task." Flag this as an open design question for OW-10's own design.md, not
   something this recon resolves.
4. **No slice-boundary criterion exists today** beyond orchestrator judgment ("very large" change) —
   OW-10 could optionally tighten this (e.g. a task-count or estimated-duration heuristic) but the
   AUDIT.md finding 4 brief doesn't ask for that; it only asks for the green-path cadence change +
   resume contract. Worth noting as explicitly out of scope if OW-10 doesn't want to also redefine
   slice boundaries.
5. **The resume contract is 100% net-new prose** — there is nothing today to correct or reconcile;
   it's a pure addition to the Failure-ladder's retry bullet (and possibly a new "fresh-executor brief
   template" subsection), with no spec-level counterpart needed (per §3's conclusion on the
   resume-contract half).
6. **`_convergence.py`'s per-task JSON state is NOT a resume mechanism** and OW-10 should not be
   confused into thinking it already provides one — it's scoped to fix-attempt/file-touch counting on
   the currently-failing test only, unrelated to "which tasks are done."
