# tasks — apply-throughput-resume (OW-10)

Apply-phase edits only. Design + acceptance: `notes.md`; anchors + current text: `recon-ow10.md`.
Spec delta authored under `specs/apply-convergence-guard/` (MODIFIED) — implement the executor-body
cadence to match its new scenarios; do NOT re-author it. **Re-grep every anchor before editing** —
OW-7 landed on `SKILL.md` just before this change, so line numbers have shifted; match on the quoted
text, not the numbers. This change is prose + two byte-synced executor-body edits — no code/tests.

## Group 1 — Executor body: green-path test cadence (BOTH files, byte-synced)

**Sync constraint (recon §2):** `scripts/test_executor_body_agreement.py` asserts the two
apply-executor bodies are byte-identical after stripping frontmatter + one sanctioned intro clause.
Step 2 is not the intro clause, so the T1 and T2 edits MUST be character-for-character identical.

- [x] **T1 — `.claude/agents/apply-executor.md` step 2.** Replace the current per-task-loop step 2
  (recon §1a — the block starting `2. **Run the project's tests** using the per-repo test command:`
  through the `**Never improvise** … wrong venv/flags.` bullet) with:
  ```
  2. **Run the project's tests.** Use the per-repo test *tool* — prefer `scripts/test-cmd`
     (one-line file in the repo root); if absent, the project's standard/documented test
     command (`pyproject.toml` pytest config, a `Makefile` `test` target, or `package.json`
     `test` script). **Never improvise** an ad-hoc command that may pick the wrong venv/flags.
     - **Per task (green-path check, first time through this task only):** run that same tool
       **scope-narrowed** to the tests covering the files this task changed — from
       `git diff --name-only`, the sibling/covering test file(s) (e.g. `<test-cmd> path/to/test_touched.py`).
       Scope-narrowing the SAME tool is NOT improvising. If the touched-module→test mapping is
       unclear, run the full command. (On a **CONTINUE retry from step 4** the existing red-path
       rule applies instead — re-run the failing test's module, not a git-diff-derived set.)
     - **Once after the whole loop (assignment gate):** this bullet fires exactly ONCE, after the
       per-task loop finishes (no `[ ]` tasks remain) — NOT on each iteration. Run the **full**
       documented command (unnarrowed) once; report success only if it passes. A red full run
       enters the red-path handling (step 4) — it does NOT complete the run.
  ```
  Keep the surrounding steps (1, 3, 4, the `CONTINUE`/`STOP` branches) UNCHANGED. The red-path
  `CONTINUE` bullet already permits "re-run only the failing test's module" — leave it as is.

- [x] **T2 — `.opencode/agents/apply-executor.md` step 2.** Apply the IDENTICAL replacement (same
  bytes) to this file's step 2 (recon §2 anchor `.opencode/agents/apply-executor.md:33-39`). After
  both edits, the two bodies must remain byte-identical (save the one sanctioned `.claude` intro
  clause, which is elsewhere). This is mechanically enforced by T5's gate.

## Group 2 — SKILL.md: the resume contract (orchestrator prose ONLY)

- [x] **T3 — Failure-ladder resume brief.** In `.claude/skills/openspec-apply-change/SKILL.md`, find
  the **Failure ladder**'s "Operational crash" retry bullet (recon §1c — the bullet starting
  `- **Operational crash** → **retry the \`opencode run\` once**` … ending `… to finish \`tasks.md\`.`).
  Replace it with the block below. **Preserve the existing indentation** — the bullet is a 6-space
  sub-item under `3. **Failure ladder:**`; keep it at that nesting (do NOT promote it to a top-level
  list item):
  ```
      - **Operational crash** → **retry the `opencode run` once with a resume brief.** The resume
        brief SHALL state: (1) which `tasks.md` items are already `[x]` — SKIP them, do not redo
        completed work; (2) resume at the first `[ ]`; (3) **reconcile the in-flight task** — the
        task at/after the last `[x]` may have been half-edited when the prior run died, so re-read
        its current on-disk state (`git diff`) and complete/repair it rather than assume it is
        untouched or already done; (4) carry forward distilled state — front-load the facts you have
        already verified as given and forbid codebase re-exploration (the wrapper is a hard ceiling;
        the executor otherwise burns its budget re-deriving context you already have). This is the
        ONLY resume path — the harness has no subagent resume (AGENTS.md "Make work resumable"), so a
        killed executor restarts cold. Second crash → spawn a **Sonnet subagent** apply-executor
        (`Agent` tool, `subagent_type: "apply-executor"`) to finish `tasks.md`, given the same brief.
  ```
  **Do NOT touch** OW-7's wrapper-invocation block (the `scripts/opencode_delegate.py` call in the
  triage numbering) or the slicing paragraph (`Bounded wait + EXIT-sentinel …`). Then in the
  **OpenCode-path** failure section, immediately after the `dispatch a **fresh** @apply-executor`
  line (recon §1c anchor — the "No declared blocker" branch), add a one-line pointer: "give the fresh
  executor the same resume brief (skip `[x]` / resume at first `[ ]` / reconcile the in-flight task /
  carry distilled state)" — do not duplicate the full block.

## Group 3 — Gate

- [x] **T4 — Executor-body/spec agreement.** Confirm the T1/T2 edits satisfy the MODIFIED
  `apply-convergence-guard` delta's two new scenarios (green-path scope-narrow permitted; full suite
  gates before completion). No code beyond the prose edits.

- [x] **T5 — Green gate.** Run `bash scripts/check.sh` → exit 0. This includes
  `test_executor_body_agreement.py` (the two executor bodies must be byte-identical — if it FAILS,
  the T1/T2 edits diverged; diff them and make them identical) and the live-tree doc lints. No ruff
  target changes (only .md edited), but run `ruff format`/`ruff check` if any `.py` was touched
  (none expected). Do NOT commit. Report: the exact `check.sh` result, and confirm
  `test_executor_body_agreement.py` passed (bodies synced).
