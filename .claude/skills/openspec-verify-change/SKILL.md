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

> **MANDATORY — behavioral review. This is the core of verify, not optional.**
> Per `AGENTS.md` and `openspec/config.yaml`, verifying a change is the orchestrator's **own** substantive behavioral review of the apply-executor's work — not a checklist rubber-stamp, and not delegated. **Steps 4–8 below ARE that behavioral review and are the core of verify** — they are mandatory and non-delegable; do NOT skip ahead to the artifact/spec mapping checks (Steps 12–18) or treat that numbered checklist as the whole job. Do not trust the executor's completion summary — trust the code, the tests, and the real output. If the behavioral review (Steps 4–8) fails, the verdict is **NEEDS REVISION** regardless of the checklist. Defect-handling detail, and the multi-model / simplicity / security gates, are in the reference subsections immediately below this preamble.

### On a defect / failure modes

**Caveats on the 5 self-review steps:**
- **(step 2) commit-test-gate backstop:** The commit-test-gate (`.claude/settings.json` `PreToolUse` hook on `git commit`) backstops the green-suite requirement — it blocks any commit whose tests are not green. A failing verify should be caught BEFORE the gate would block, making the gate the known last-resort enforcement rather than the first line.
- **(step 4) why the live smoke is mandatory:** The mock-based suite is *structurally blind* to whether the mocks match reality — a fully green suite can encode a **wrong** API contract (wrong sort semantics, wrong field types, wrong error codes) and so pass while the real integration collects nothing. This is the mock-encoded-idealized-API failure mode — the full war-story is the canonical mock-contract rule in `.claude/agents/apply-executor.md` (do not restate it here). Therefore: run the change's opt-in live test (e.g. `LIVE_TESTS=1 .venv/bin/python -m pytest tests/test_<x>.py -k live -v`) and inspect a real response.
- **(step 5) do not hand-fix:** Do **not** hand-fix beyond a trivial typo / comment / one-line rename — if you would write more than one line of implementation, stop and re-delegate.

**Fix-redelegation mechanics (Claude Code):**
- **Claude Code:** the fresh fix executor is the deepseek `apply-executor` driven via `opencode run` (same invocation shape as in the apply skill's Step 6, but the prompt is the **self-contained fix-spec** for the specific defect, not the whole `tasks.md`). **One attempt.**
- **Wrap the call in `timeout -k 30 600 opencode run --dir <repoRoot> --agent apply-executor --model deepseek/deepseek-v4-flash --format json <fix-spec> > /tmp/fix-out.jsonl 2> /tmp/fix-err.log < /dev/null`** (a scoped single-defect fix has a 10-minute budget matching the apply/archive floor). Per `.claude/skills/_shared/delegation-harness.md` §a (hardened invocation) and §c (surgical kill — never `pkill`); budget 600s with `-k 30` per the table in §e. A `timeout` kill (exit 124, or 137 if SIGKILL was needed) counts as the operational failure in the next bullet → escalate to Sonnet.
- **Completion detection.** Per `.claude/skills/_shared/delegation-harness.md` §d (EXIT-sentinel): append `; echo "EXIT=$?" > /tmp/fix-out.exit`, detect completion by `[ -f /tmp/fix-out.exit ]`. Never poll with pgrep or judge from a mid-execution snapshot. Also note: scoped fix runs have repeatedly completed their work and still exited 1 at session teardown — judge success from disk (`git diff`, tests), not the exit code alone.
- **Assert the real agent ran (§b) + extract completion text via wrapper:**
  Invoke `scripts/opencode_delegate.py` for post-processing, which detects fallback,
  extracts the completion text, and classifies status (see the harness §b contract):
  ```bash
  scripts/opencode_delegate.py \
    --phase verify-fix --agent apply-executor --model deepseek/deepseek-v4-flash --change <name> \
    --out /tmp/fix-out.jsonl --err /tmp/fix-err.log \
    --exit-file /tmp/fix-out.exit \
    --quiet
  ```
  Read the extracted text from `/tmp/fix-out.jsonl.text.txt`. Confirm parseable;
  empty/unparseable → operational crash (escalate to Sonnet).

**Escalation rungs:**
- **Escalate to a Sonnet subagent** if that one attempt yields **either**: (a) an operational failure (crash / no usable output), **or** (b) a quality failure — i.e. the orchestrator's re-verification (re-run from MANDATORY step 1) still finds the defect, or finds a newly-introduced one.
- After Sonnet fixes it, re-verify again from step 1.
- **Mandatory disclosure:** if Sonnet was used, say so in the verification report / `notes.md` field 3 ("defect found and how it was fixed — and who fixed it"), explicitly noting the deepseek attempt failed and Sonnet took over.

### Multi-model passes (independent verification gates)

**Tier applicability:** This skill and its multi-model passes apply to MEDIUM and COMPLEX changes only. A SMALL change does its own verification per `AGENTS.md` and does **not** invoke this skill, its multi-model passes, or the verify phase-gate.

After your own self-review (above) and **before** the artifact/spec mapping checklist Steps below, you MUST run independent multi-model verification passes. These passes are additional independent confirmations; they do NOT replace your own self-review — the "do not delegate this" rule above still governs the self-review.

The pass sequence is identical on both platforms (Claude Code and OpenCode) and depends on tier:

- **MEDIUM:** self-review → `deepseek/deepseek-v4-pro` behavioral verifier pass.
- **COMPLEX:** self-review → `deepseek/deepseek-v4-pro` behavioral verifier pass → `deepseek/deepseek-v4-flash` lens verifier pass (see the lens-pass subsection below).

No pass repeats the behavioral checklist a third time — the recorded three-repo evidence showed zero non-trivial unique catches from a same-checklist third pass.

The verifier agent is defined in `.opencode/agents/openspec-verifier.md` (default `model: deepseek/deepseek-v4-flash`; `bash: a destructive-command denylist (catch-all allow)`, `edit: deny`). The verifier runs the review its invocation prompt specifies (behavioral by default; lens for the lens pass), but it **never modifies files** — it reports defects and emits a machine-discriminable verdict block of this form:

```
## Verify Pass — <model-id>
VERDICT: READY            # or exactly: VERDICT: NEEDS REVISION
### Defects
- 🔴 <file:line> — <what is wrong and the evidence>     # `- None` when clean; the section is always present
```

#### Invocation (both platforms)

For each pass, invoke the verifier via an `opencode run` with hardened invocation and EXIT-sentinel per `.claude/skills/_shared/delegation-harness.md` §a and §d (same pattern as the fix-executor invocation above):

**Behavioral pro pass (MEDIUM and COMPLEX):**
```bash
timeout -k 15 780 opencode run --dir <repoRoot> --agent openspec-verifier \
  --model deepseek/deepseek-v4-pro --format json "<behavioral verifier prompt>" \
  > /tmp/verify-pro-out.jsonl 2> /tmp/verify-pro-err.log < /dev/null ; echo "EXIT=$?" > /tmp/verify-pro-out.exit
```

**Lens pass (COMPLEX only):**
```bash
timeout -k 15 780 opencode run --dir <repoRoot> --agent openspec-verifier \
  --model deepseek/deepseek-v4-flash --format json "<lens prompt>" \
  > /tmp/verify-lens-out.jsonl 2> /tmp/verify-lens-err.log < /dev/null ; echo "EXIT=$?" > /tmp/verify-lens-out.exit
```

Both invocations follow the hardened invocation and EXIT-sentinel patterns per `.claude/skills/_shared/delegation-harness.md` §a and §d.

#### Behavioral verifier prompt

Use this prompt for the behavioral pro pass:

```text
You are the OpenSpec Change Verifier. Perform the behavioral verification review:

1. Read the git diff and changed files. Open every file the executor touched. Trust the code, not any summary.
2. Re-run the FULL test suite via the per-repo command — prefer `scripts/test-cmd`; when absent, use the project's documented test command (e.g. check `pyproject.toml` for pytest config, `Makefile` for a `test` target, or `package.json` for a `test` script). Never improvise an ad-hoc `pytest` or other command that may pick the wrong venv/flags.
3. Eyeball a concrete real-output sample — the actual records, rows, text, or values the change produces. Do not just confirm tests pass.
4. For any external-API surface, run the live smoke against the real endpoint. A skipped live smoke is not a passed one. If the change has no live smoke, that is itself a critical gap.

Emit your verdict in the ## Verify Pass — <model-id> block format, with VERDICT: READY or VERDICT: NEEDS REVISION and an always-present ### Defects section.
```

#### Lens pass (COMPLEX)

This subsection applies to COMPLEX changes only (and optionally to MEDIUM changes at the orchestrator's discretion). The lens pass runs the `deepseek/deepseek-v4-flash` model with a fixed prompt asking questions the behavioral checklist does not ask — a different checklist, not a third run of the same one.

The orchestrator SHALL select one lens per change and record the selection with a one-line rationale in `review-log.md`. The lens pass is **diff-scoped**: it is NOT required to re-run the full test suite (the pro behavioral pass already did) and MAY run targeted probes scoped to its lens questions. Its findings are leads the orchestrator confirms from disk. It retains the hard-gate and recovery semantics of the other passes.

**Default — test-quality/adversarial-oracle lens:**
```text
You are the OpenSpec Change Verifier performing a test-quality lens pass. Focus on test integrity:

FIRST run `checks.py --check test-quality` (from the repo root) and confirm its findings from disk — these are the mechanical test-smell results the detector already found.

THEN, for each test the change adds or modifies, apply the residual lens judgment: would the test fail if the behavior it claims to cover broke? Name the assertion that would trip. Specifically flag:
- Tautological or forced-green assertions (e.g. `assert True`, `assert 1 == 1`) — the detector catches these already; confirm its findings
- Empty test bodies or tests that never reach their assertion
- Mocks that replace the module under test (self-mocking)
- Discarded return values or flags (e.g. calling a function but ignoring its return)
- Unfrozen clocks in time-sensitive tests

Emit your findings in the standard ## Verify Pass — <model-id> / VERDICT: / ### Defects block.
```

**Data-scale lens (for data-path-dominant changes):**
```text
You are the OpenSpec Change Verifier performing a data-scale lens pass. Focus on data-path safety:

FIRST run `checks.py --check data-scale` (from the repo root) and confirm its findings from disk — the mechanical `.fetchall()` results the detector already found.

THEN apply the residual lens judgment the detector cannot make mechanically:
- Which input domains are unbounded in production?
- Does the change fully materialize the result of an unbounded query (e.g. `fetchall()` on an unbounded query)?
- Does the change need an at-scale run or a recorded bounded-domain argument in `notes.md`?

Emit your findings in the standard ## Verify Pass — <model-id> / VERDICT: / ### Defects block.
```

**Selection rule:** select the test-quality lens by default. Select the data-scale lens when the change's dominant risk is data-path behavior (unbounded inputs, query volume, large-scale processing). The orchestrator MAY additionally run a lens pass on a MEDIUM change when its risk profile warrants it, under the same contract and recording rules.

**Forward-compatibility (fulfilled):** the corresponding deterministic detectors now exist (`checks.py --check test-quality` and `checks.py --check data-scale`). Each lens prompt above directs the verifier to run and confirm the detector's findings rather than rediscover them.

#### Assert the real verifier ran (post-processing via wrapper)

Before trusting any pass output (both platforms), invoke `scripts/opencode_delegate.py`
for post-processing, which detects fallback, extracts the completion text, classifies
status, and asserts markers (see the harness §b contract):

**Behavioral pro pass:**
```bash
scripts/opencode_delegate.py \
  --phase verify-pro --agent openspec-verifier --model deepseek/deepseek-v4-pro --change <name> \
  --out /tmp/verify-pro-out.jsonl --err /tmp/verify-pro-err.log \
  --exit-file /tmp/verify-pro-out.exit \
  --require-marker "## Verify Pass" --require-marker "VERDICT:" \
  --verdict-regex "VERDICT: (READY|NEEDS REVISION)" \
  --quiet
```

**Lens pass (COMPLEX only):**
```bash
scripts/opencode_delegate.py \
  --phase verify-lens --agent openspec-verifier --model deepseek/deepseek-v4-flash --change <name> \
  --out /tmp/verify-lens-out.jsonl --err /tmp/verify-lens-err.log \
  --exit-file /tmp/verify-lens-out.exit \
  --require-marker "## Verify Pass" --require-marker "VERDICT:" \
  --verdict-regex "VERDICT: (READY|NEEDS REVISION)" \
  --tag lens=<test-quality|data-scale> \
  --quiet
```

Read the extracted text from the respective `--text-out` default (`verify-pro-out.jsonl.text.txt`
or `verify-lens-out.jsonl.text.txt`). Confirm parseable; empty/unparseable → operational crash.
Then confirm the extracted output contains a `## Verify Pass` heading AND a `VERDICT:` line
(the wrapper's `--require-marker` flags already assert these; this is the orchestrator's
own confirmation).

#### Judge findings from disk

Treat every verifier finding as a **lead to confirm from disk**, not gospel. Use `git diff` and re-run tests/output to reproduce each reported defect. You MAY overrule a demonstrably false finding, but you MUST record the rationale in `review-log.md` / `notes.md` (mirrors the propose "reviewer can be wrong" rule).

#### Gate semantics and recovery

Each pass is a **hard gate**. When a pass returns `VERDICT: NEEDS REVISION` and you confirm the defect from disk:

1. **Fix** via the **existing** defect re-delegation path already documented in this skill (re-delegate a self-contained fix-spec to the apply-executor; one attempt; escalate to a Sonnet subagent on operational or quality failure; disclose if Sonnet was used).
2. **Re-run the pass that failed and every pass after it**, in sequence — never the passes before it. (MEDIUM: if the pro pass fails, re-run only the pro pass — it is the only and last delegated pass. COMPLEX: if the pro pass fails, fix, re-run pro then the lens pass; if the lens pass fails, fix, re-run just the lens pass.)
3. **Loop bound:** if the **same** pass returns NEEDS REVISION across **3** fix cycles without clearing, STOP and escalate to the operator with the accumulated verdicts.

If your own self-review (pass 1, above) finds a defect, follow the existing behavioral-review-fails path: fix, re-run from pass 1 (the self-review).

### Simplicity/quality gate (MEDIUM/COMPLEX)

After the verifier passes return READY and **before** the artifact/spec mapping checklist, the orchestrator SHALL run a harness-neutral simplicity/duplication/dead-code review of the change's `git diff`:

- **Under Claude Code:** the orchestrator invokes the `simplify` (or `/code-review`) skill on the change's `git diff` and folds confirmed findings into the defect path.
- **Under OpenCode (no such skill exists):** the orchestrator itself reviews the `git diff` against this concrete checklist — (a) code duplicating functionality that already exists elsewhere in the repo; (b) abstractions introduced but used only once; (c) dead or unreachable code paths; (d) over-parameterization/config beyond the change's actual scope.

Findings are leads to confirm from disk (same discipline as verifier findings); a confirmed simplification defect uses the existing defect re-delegation path. This gate does **not** block on pure style nits — it targets over-engineering, duplication, and dead code.

### Security review (conditional — sensitive-surface changes)

When the change touches auth, credentials/secrets, persisted data, or an external API/network surface, the orchestrator SHALL run a harness-neutral security review before declaring READY:

- **Under Claude Code:** invoke the `security-review` skill on the diff.
- **Under OpenCode (no such skill exists):** the orchestrator itself reviews the diff against this concrete checklist — (a) authn/authz bypass or missing authorization on new endpoints/queries; (b) credential/secret leakage (logged, returned in a response, or committed); (c) unsanitized external/user input reaching SQL, shell, or file paths (injection); (d) unsafe deserialization; (e) missing input-confirmation guard on a destructive operation.

This is a **hard gate for COMPLEX** changes on those surfaces and a **recommended** pass for MEDIUM changes on those surfaces. Changes touching none of those surfaces do not trigger it. Confirmed findings use the existing defect re-delegation path.

### Data-path verify rule (conditional — data-path changes)

When a change modifies a data path (a query, bulk transform, or any code whose input volume can grow with data or history), verify SHALL require the change's `notes.md` to record EITHER evidence of an at-scale run OR an explicit bounded-domain argument (why the input is bounded in production). This is the standing enforcement of the canonical "Mind data scale" rule — see `AGENTS.md` (the "Mind data scale" span) and `openspec/config.yaml` `rules.verify` — cited, not restated.

Absence of both, on a data-path change, is a verify defect the orchestrator resolves before archive. Changes touching no data path do not trigger it. Confirmed findings use the existing defect re-delegation path.

**PHASE GATE — STOP after verification.** Once the verification report and `notes.md` checkpoint are complete, without an explicit autonomy grant this is a hard STOP: tell the user the verdict and prompt them: "Verification complete. Say 'archive <name>' when ready to archive." Then WAIT. Under an autonomy grant, auto-advance to archive is permitted per the `autonomy-phase-advance` canonical rule (AGENTS.md) EXCEPT across a premise DISSENT, an unresolved verify NEEDS-REVISION, or an operator-named gate — the NEEDS-REVISION carve-out is especially relevant here: a verdict this skill's own defect loop could not clear halts the grant and surfaces to the operator instead of auto-advancing to archive.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **Select the change**

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

4. **Read the actual diffs and changed files**

   **Steps 4–8 — behavioral review: mandatory, do not delegate, do not trust the executor's summary.**

   Run `git diff` (and open the files) for everything the executor touched. Trust the code, not the summary.

5. **Re-run the FULL test suite yourself**

   Prefer `scripts/test-cmd`, falling back to the project's documented test command when absent — never an improvised command; e.g. `.venv/bin/python -m pytest -q`. It must be green (pre-existing skips OK). A green exit is **necessary but not sufficient.**

   **Point-of-action delegation cue** (cites `delegation-by-default`, AGENTS.md): the *run+extract*
   of the suite — producing the green/fail signal — is delegable to a haiku/Sonnet subagent; the
   behavioral **judgment** that follows — does the output match the oracle — is Steps 4–8's
   mandatory, **NON-delegable** core and stays with the orchestrator.

6. **Eyeball the real output the code produces**

   Render a concrete sample of what the change actually generates — the actual records/rows selected, the text or prompt produced, the request sent, the values computed — not just that tests pass. Run the relevant project command or a `scripts/_*_oneoff.py` probe against real data and inspect a real sample. Bugs that logic-reading misses are often visible the instant you render real output.

7. **If the change touches an external API / network service, run its live smoke**

   **If the change touches an external API / network service, RUN ITS LIVE SMOKE yourself against the real endpoint.** Inspect a real response. **A *skipped* live smoke is NOT a *passed* one.** If an external-API change has no live smoke at all, that is itself a **CRITICAL** gap — require one to be added before archive.

8. **On any defect**

   Diagnose and scope it yourself (reproduce it, run DB queries, read diffs), then **re-delegate the fix to a FRESH apply-executor** with a self-contained fix-spec that cites the exact file:line evidence and the concrete fix. Then re-verify from step 1.

   See **On a defect / failure modes** above for the fix-redelegation mechanics and escalation rungs.

9. **Run the independent multi-model verification passes (MEDIUM/COMPLEX only)**

   MEDIUM/COMPLEX changes run the passes in **Multi-model passes** above (SMALL does not); run them here, after the behavioral review and before the artifact/spec mapping checks below. Do NOT duplicate the invocations — point to the section.

10. **Run the simplicity/quality gate (MEDIUM/COMPLEX only)**

    MEDIUM/COMPLEX changes run the gate in **Simplicity/quality gate** above, after the multi-model passes and before the artifact/spec mapping checks below. Do NOT duplicate the review — point to the section.

11. **Run the security review (conditional)**

    Run the review in **Security review** above when the change touches auth, credentials/secrets, persisted data, or an external API/network surface. It is a **hard gate for COMPLEX** changes on those surfaces and a **recommended** pass for MEDIUM. Do NOT duplicate the review — point to the section.

12. **Initialize verification report structure**

    Create a report structure with three dimensions:
    - **Completeness**: Track tasks and spec coverage
    - **Correctness**: Track requirement implementation and scenario coverage
    - **Coherence**: Track design adherence and pattern consistency

    Each dimension can have CRITICAL, WARNING, or SUGGESTION issues.

13. **Verify Completeness**

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
      in design.md's **Verification** section, not in `tasks.md`. (Rule canonical: `openspec/config.yaml` `rules.tasks`.)

    **Spec Coverage**:
    - If delta specs exist in `contextFiles.specs`:
      - Extract all requirements (marked with "### Requirement:")
      - For each requirement:
        - Search codebase for keywords related to the requirement
        - Assess if implementation likely exists
      - If requirements appear unimplemented:
        - Add CRITICAL issue: "Requirement not found: <requirement name>"
        - Recommendation: "Implement requirement X: <description>"

14. **Verify Correctness**

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

15. **Verify Coherence**

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

16. **Generate Verification Report**

    **Multi-model passes**:
    - After the self-review and any delegated verifier passes (see the multi-model passes section above), record each pass's verdict in the report: pass number, model that ran it, verdict, and which defects (if any) it surfaced. For a lens pass, also record which lens was selected and the orchestrator's one-line rationale.
    - For any pass that was re-run after a fix, record BOTH the original NEEDS REVISION verdict and the final READY verdict.

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

17. **Checkpoint verify findings to the change dir (MANDATORY before archive handoff)**

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
       inline), attributed to the pass/model that surfaced it (self-review, pro pass, or lens pass);
    4. any **as-built delta discovered during verify** that the artifacts don't already record;
    5. **forward-looking items for the project docs — the load-bearing, easily-missed one.** Enumerate
       every **open question, tuning item, deferred-scope decision, follow-on, or monitored risk** that
       surfaced during design OR verify and is **recorded nowhere else** (not in `proposal.md` /
       `design.md` / `specs/` and not already in `knowledge/questions/INDEX.md`). These exist to be folded
       into `knowledge/questions/INDEX.md` (and where relevant `knowledge/decisions/INDEX.md`) at archive. Be
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
    must still reconcile: `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`, `knowledge/questions/INDEX.md`, spec
    promotion into `openspec/specs/`, and any cleanup). Do NOT edit those project-tracked docs yourself
    here — they are reconciled at archive per the write-discipline rule; your job at verify is to make
    the change dir self-sufficient so that reconciliation loses nothing.

    Why this is mandatory: per `AGENTS.md`, archive is reconciled by a **delegated
    deepseek-v4-pro archive-executor (fresh context), then primary-reviewed**. That executor reads
    the change dir, not this conversation. Verify is the step that manufactures these durable facts,
    and anything left only in this context **dies at the session boundary** — the archive-executor
    is blind to it. **Field 5 is the one that bites:** a new open-question or tuning item that
    exists only in this conversation is simply *lost* — it never reaches `knowledge/questions/INDEX.md`, and
    the project silently forgets a decision it meant to revisit. This write is cheap because the
    context is already loaded. Do not skip it even when the verdict is a clean pass.

18. **Verbally acknowledge documentation persistence (MANDATORY — do not end the turn without it)**

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
      Still owned by archive — <knowledge/STATUS.md, knowledge/decisions/INDEX.md, knowledge/questions/INDEX.md, spec promotion, cleanup>
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
- **PHASE GATE**: When verification is complete, without an autonomy grant this is a hard STOP — inform the user and prompt them for the next step. Under a grant, auto-advance to archive per the `autonomy-phase-advance` rule (AGENTS.md), EXCEPT across a premise DISSENT, an unresolved verify NEEDS-REVISION, or an operator-named gate (the NEEDS-REVISION carve-out is especially relevant here).
