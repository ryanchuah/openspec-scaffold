<!-- Apply-phase implementation ONLY. Spec promotion (openspec/specs/) is archive work, not
     apply. AGENTS.md and README.md ARE part of the shipped instruction surface, so editing them
     is apply work (not the archive doc reconciliation, which covers STATUS.md / ai-docs/* only).
     Behavioral acceptance (design.md Verification V1–V6) is checked at verify, not here.
     Do §1 → §2 → §3 → §4 in order (§2 references the agent created in §1). -->

## 1. Verifier agent

- [x] 1.1 Create `.opencode/agents/openspec-verifier.md`. The frontmatter MUST be exactly this (the permission block is load-bearing — see design D4; do not add or omit keys):
  ```yaml
  ---
  name: openspec-verifier
  description: OpenSpec Change Verifier — runs the behavioral verify review (read diffs, re-run the full suite, eyeball real output, run live smoke) as an independent multi-model pass and emits a machine-discriminable verdict. Read-only on files; never fixes. Invoked by the primary agent during the verify phase — do not invoke directly.
  mode: all
  model: deepseek/deepseek-v4-flash
  permission:
    read: allow
    edit: deny
    glob: allow
    grep: allow
    list: allow
    bash: allow
    task: deny
    webfetch: deny
    websearch: deny
    external_directory:
      "*": deny
      "/tmp/**": allow
  ---
  ```
  The body MUST instruct the verifier per design D5: read the `git diff` and changed files; re-run the FULL test suite via the per-repo command (`scripts/test-cmd` or the project's documented command, never improvised); eyeball a concrete real-output sample; for any external-API surface run the live smoke (a skipped smoke is NOT a pass; a missing smoke on an external-API change is itself a critical defect); **never modify files — report defects, do not fix them**; and emit exactly a verdict block of the form:
  ```
  ## Verify Pass — <model-id>
  VERDICT: READY            # or exactly: VERDICT: NEEDS REVISION
  ### Defects
  - 🔴 <file:line> — <what is wrong and the evidence>     # `- None` when clean; the section is always present
  ```
  Acceptance: file exists; `grep -E 'bash: allow|edit: deny|task: deny' .opencode/agents/openspec-verifier.md` matches all three; the `external_directory` block lists `"*": deny` before `/tmp/**: allow`; default `model:` is `deepseek/deepseek-v4-flash`; body documents the read-only behavioral review and the `## Verify Pass` / `VERDICT:` block; **body explicitly contains the "never modify files / do not fix" prohibition** (`grep -iE 'never modify|do not fix' .opencode/agents/openspec-verifier.md` matches). (~20 min)

## 2. Wire the verify skill

- [x] 2.1 In `.claude/skills/openspec-verify-change/SKILL.md`, insert a new MANDATORY section for the multi-model passes **immediately after the behavioral-review blockquote** (the block that ends `...the verdict is **NEEDS REVISION** regardless of the checklist.`) and **before** the `**PHASE GATE — STOP after verification.**` line. The section MUST cover, per design D1–D7:
  - That the passes run after the self-review (the blockquote above) and before the artifact/spec mapping checklist Steps below; the self-review is unchanged and still not delegated.
  - The two platform chains: **Claude Code** orchestrator → self → `deepseek/deepseek-v4-pro` pass → `deepseek/deepseek-v4-flash` pass; **OpenCode** orchestrator → self → `deepseek/deepseek-v4-flash` pass only (with the model-diversity rationale).
  - The exact Claude Code invocation for each pass (the EXIT-sentinel/background pattern matches the existing fix-executor invocation in this same skill), e.g. for the pro pass:
    ```bash
    timeout -k 15 780 opencode run --dir <repoRoot> --agent openspec-verifier \
      --model deepseek/deepseek-v4-pro --format json "<the fixed verifier prompt from design D5>" \
      > /tmp/verify-pro-out.jsonl 2> /tmp/verify-pro-err.log < /dev/null ; echo "EXIT=$?" > /tmp/verify-pro-out.exit
    ```
    and the flash pass identically with `--model deepseek/deepseek-v4-flash` and `/tmp/verify-flash-*` paths.
  - The OpenCode path: spawn `subagent_type: openspec-verifier` via the Task tool (runs the frontmatter default flash, no override); it is in-process and NOT subject to the `< /dev/null` / `--dir` hardening.
  - Assert the real verifier ran before trusting output. **For the Claude Code `opencode run` passes:** `grep -q "Falling back to default agent"` on the pass's stderr → escalate; then confirm the extracted text has a `## Verify Pass` heading AND a `VERDICT:` line. **For the OpenCode Task-tool path** (in-process; no `opencode run` stderr to grep): use the format check alone (`## Verify Pass` + `VERDICT:`). Judge every finding **from disk** (`git diff` / re-run); may overrule a demonstrably false finding only with recorded rationale.
  - Gate + recovery: each pass is a hard gate; on `VERDICT: NEEDS REVISION` (confirmed from disk) fix via the **existing** defect re-delegation path already documented in this skill, then **re-run the failed pass and every pass after it**, never earlier ones; if the same pass fails across **3** fix cycles, STOP and escalate to the operator.

  Acceptance: the new section exists between the behavioral-review blockquote and the PHASE GATE line; both chains are documented; each documented Claude `opencode run` verifier invocation contains `< /dev/null`, `--dir`, AND the EXIT-file sentinel (`echo "EXIT=$?"`); the section states the fallback-warning stderr grep applies to the `opencode run` passes only (the Task-tool path uses the format check alone); the `## Verify Pass` / `VERDICT:` format, the assert-real-verifier-ran checks, and the rerun-failed-and-after + 3-cycle-bound semantics are all present. (~60 min)

- [x] 2.2 In the same skill, extend the report step (step 8 "Generate Verification Report") and the `notes.md` checkpoint step (step 9) so both record, per pass, the model that ran it, its verdict, and which pass surfaced each defect found/fixed — and, for any pass re-run after a fix, record BOTH the original NEEDS REVISION and the final READY verdict (design D8 + the spec's audit-trail scenarios). Acceptance: step 8 and step 9 each reference the per-pass multi-model audit trail. (~20 min)

## 3. Reconcile the instruction surface

- [x] 3.1 Update `AGENTS.md` to add the `openspec-verifier` to the delegation roles alongside the reviewer/apply-executor/archive-executor, and describe the multi-model verify gate (Claude self→pro→flash; OpenCode self→flash; verifier is read-only, bash-capable, edit-denied). Keep the existing entries intact. Acceptance: `AGENTS.md` names `openspec-verifier` and describes the verify gate chain. (~15 min)

- [x] 3.2 Update `README.md` so the verify row/section of the workflow describes the multi-model verifier passes (the two platform chains) alongside the existing reviewer/executor delegation. Acceptance: `README.md` mentions the verify verifier passes and the pro/flash chain. (~15 min)

## 4. Validate (no regression)

- [x] 4.1 Run `openspec validate verify-multimodel-gate --strict` → must report valid. Run the repo's test suite via the per-repo command (`scripts/test-cmd` or the documented command) → must be green (this is a markdown/agent-config change; it must not regress existing tests). Acceptance: validate exits 0 and the suite is green. (~10 min)
