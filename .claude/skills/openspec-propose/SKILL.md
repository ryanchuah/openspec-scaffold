---
name: openspec-propose
description: Propose a new change with artifacts generated sequentially and reviewed before freeze. Use when the user wants to describe what they want to build and get a complete, reviewed proposal with design, specs, and tasks ready for implementation.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Propose a new change — create artifacts one at a time, freeze each after review, then generate the next.

I'll create artifacts with review:
- proposal.md (what & why) → review → freeze
- design.md (how — include a **Verification** section stating the change-specific acceptance criteria) → review → freeze
- tasks.md (apply-phase implementation steps ONLY — code, tests, scripts) → review → freeze

**CRITICAL — Do NOT batch-create all artifacts.** Create proposal, review it, fix it, freeze it. Only then create design (using the frozen proposal as context). Repeat for tasks. Downstream artifacts written before upstream ones are frozen will contain stale decisions, requiring extra review rounds to correct. Each unnecessary review round costs real money.

**PHASE GATE — STOP after proposing.** Once all artifacts are frozen, you MUST NOT automatically proceed to implementation. Tell the user "All artifacts created, reviewed, and frozen. Ready for implementation. Say 'apply <name>' when you want me to start." Then WAIT. Never invoke implementation without an explicit user request. Crossing phases without permission is a hard rule.

---

**Input**: The user's request should include a change name (kebab-case) OR a description of what they want to build.

**Steps**

1. **If no clear input provided, ask what they want to build**

   Use the **AskUserQuestion tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Create the change directory**
   ```bash
   openspec new change "<name>"
   ```
   This creates a scaffolded change in the planning home resolved by the CLI with `.openspec.yaml`.

3. **Get the artifact build order**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to get:
   - `applyRequires`: array of artifact IDs needed before implementation (e.g., `["tasks"]`)
   - `artifacts`: list of all artifacts with their status and dependencies
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context. Use these instead of assuming repo-local paths.

4. **Create artifacts in sequence until apply-ready**

   Track progress through the artifacts with a running checklist (your harness's todo tool, if it has one).

   Loop through artifacts in dependency order (artifacts with no pending dependencies first):

   a. **For each artifact that is `ready` (dependencies satisfied)**:
      - Get instructions:
        ```bash
        openspec instructions <artifact-id> --change "<name>" --json
        ```
      - The instructions JSON includes:
        - `context`: Project background (constraints for you - do NOT include in output)
        - `rules`: Artifact-specific rules (constraints for you - do NOT include in output)
        - `template`: The structure to use for your output file
        - `instruction`: Schema-specific guidance for this artifact type
        - `resolvedOutputPath`: Resolved path or pattern to write the artifact
        - `dependencies`: Completed artifacts to read for context
      - Read any completed dependency files for context
      - Create the artifact file using `template` as the structure and write it to `resolvedOutputPath`
      - Apply `context` and `rules` as constraints - but do NOT copy them into the file
      - **DESIGN.MD ONLY — External-API live probe before self-review.** If the design
        introduces or touches an external-API surface — a new kwarg, client option, or
        changed request shape — run a live probe of that EXACT surface against the real
        installed environment before the self-review step. The mock-based test suite is
        structurally blind to whether the real library honors the assumptions: for
        example, a constructor kwarg was assumed available, the reviewer "confirmed" it,
        the full patched test suite passed green, and the real library crashed on the
        first request. The probe must exercise a real request
        (constructing a client is NOT proof — failures can defer to request time,
        exactly what bit `_build_client()`). Record the probe in a `### Live Probe`
        section of design.md with the command run and observed output. If the probe
        reveals the assumption is wrong, fix the design before proceeding — do not
        self-review or invoke the reviewer on a known-false claim. Skip this step only
        when the change has zero new external-API surface.
      - Show brief progress: "Created <artifact-id>"

    b. **Self-review the artifact before invoking the reviewer.**
       - Re-read the artifact you just wrote and check it for correctness against the dependencies, template, and context
       - Verify every claim is concrete and implementable, every decision resolves an ambiguity, every scope boundary is explicit
       - Fix any obvious issues you find yourself before calling the reviewer
       - This is the first review pass (out of max 4: 1 self + up to 3 `@openspec-reviewer` passes)

    c. **Invoke `@openspec-reviewer` to audit the artifact.**

       The path forks based on which agent platform you are:

       ---
       ### If you are Claude Code (claude-cli)

        Claude Code cannot spawn non-Anthropic subagents. Instead, invoke the
        reviewer programmatically via `opencode run`. Do NOT review the artifact
        yourself — the review must come from a different model.

          1. Run the reviewer (substituting actual paths for `<changeRoot>` and
             `<artifact>`), **capturing stdout and stderr to separate files**.
             Per `.claude/skills/_shared/delegation-harness.md` §a (hardened invocation): `< /dev/null`
             + `--dir <repoRoot>`. Budget 780s with `-k 15` per the table in §e.

             timeout -k 15 780 opencode run \
               --dir <repoRoot> \
               --agent openspec-reviewer \
               --model deepseek/deepseek-v4-pro \
               --format json \
               "Review the artifact at <changeRoot>/<artifact>.md. \
                Also read the explore-brief if it exists and openspec/specs/ \
                for context." \
               > /tmp/review-out.jsonl 2> /tmp/review-err.log < /dev/null

             If the user specified a different reviewer model, substitute it
             for `deepseek/deepseek-v4-pro`. The `--agent` flag loads the
             reviewer's role prompt and tools; `--model` selects which LLM runs.

             **Bounded wait + surgical kill.** Per `.claude/skills/_shared/delegation-harness.md` §c
             (surgical kill — never `pkill`). A timeout surfaces as exit code 124
             (or 137 if SIGKILL was needed) — treat it per step 4's salvage path
             (do NOT simply escalate).

         2. **Assert the real reviewer actually ran:** Per `.claude/skills/_shared/delegation-harness.md`
            §b (grep stderr for `Falling back to default agent`, extract `part.text` via
            `jq`, confirm parseable). Then add the reviewer-specific format check:
            confirm the extracted text contains a `## Review Round` heading AND at least
            one severity marker (🔴/🟡/💡). If either is missing, the output did not come
            from the reviewer prompt: do NOT proceed, escalate with the raw output.

        3. Process the review:
           - Append the review text to `review-log.md` with round number
             and date
           - When a fix is required in the artifact, make it a **concrete,
             implementable decision**, not a paraphrase of the problem. E.g.,
             instead of "return value semantics differ" (paraphrase), decide:
             "returns 0 — zero Document rows inserted" (concrete). If a
             reviewer flags a gap, close it with a specific choice.
           - If 🔴 blocking issues exist → fix them in the artifact → **go back
             to step 1 for a fresh review pass. Re-review is MANDATORY.** A fix
             you made to clear a 🔴 is never self-certified — you may NOT freeze
             the artifact on the strength of your own fix. Only a review round
             that comes back with zero 🔴 can freeze it. (Max 3 reviewer passes
             total; escalate to user if still unresolved after 3.)
           - If no 🔴 issues → the artifact is frozen; move to the next one

         4. If `opencode run` fails (non-zero exit, timeout, or no review text):
            do NOT self-review. Salvage whatever review text was emitted:
            - Extract partial review text from the jsonl:
              ```bash
              grep '"type":"text"' /tmp/review-out.jsonl | jq -r '.part.text' \
                > /tmp/review-partial.txt 2>/dev/null || true
              ```
            - If partial text exists, append it to `review-log.md` marked with
              `**PARTIAL — reviewer timed out**` at the top of the block.
            - **Decide: re-run or escalate.** If the partial review contains at
              least one finding (🔴/🟡/💡) OR the reviewer ran for more than
              120s before being killed → re-run ONCE at full budget (go back to
              step 1 of the invocation). If the partial has zero findings and
              was killed in under 120s → escalate to the user with the partial
              output, exit code, and stderr.

       ---
       ### If you are OpenCode

       Use the Task tool with `subagent_type: "openspec-reviewer"` to audit
       the artifact:

       - Append the review output to `review-log.md`
       - When a fix is required, make it a **concrete, implementable
         decision**, not a paraphrase of the problem. E.g., instead of
         "return value semantics differ" (paraphrase), decide: "returns 0 —
         zero Document rows inserted" (concrete). If a reviewer flags a gap,
         close it with a specific choice.
       - If 🔴 blocking issues exist → fix them in the artifact → **re-review is
         MANDATORY** — invoke the reviewer again. A fix you made to clear a 🔴 is
         never self-certified: you may NOT freeze the artifact on the strength of
         your own fix. Only a review round that comes back with zero 🔴 can freeze
         it. (Max 3 reviewer passes; escalate to user if still unresolved after 3.)
       - If no 🔴 issues → the artifact is frozen; move to the next one
       - **If the reviewer subagent fails for any reason** (model not found,
         provider error, timeout, etc.): do NOT self-review as a replacement.
         Halt immediately and escalate to the user with the exact error.

       ---
       **Never skip review or batch-create downstream artifacts.** A design
       written against an unfrozen proposal will reference stale decisions,
       causing extra review rounds on every downstream artifact.

       **The reviewer can be wrong — apply judgment, don't obey blindly.** If a
       finding (including a 🔴) contradicts the authoritative `openspec
       instructions <artifact>` template, the project's own rules (AGENTS.md /
       skill guardrails), or a verifiable fact in the codebase, the primary MAY
       overrule it — but MUST record the rejection and its concrete rationale in
       `review-log.md`, and MUST NOT freeze on a genuine defect just to move on.
       Mechanically complying with a false finding causes its own rework.

    d. **Continue until all `applyRequires` artifacts are complete**
       - After creating each artifact, re-run `openspec status --change "<name>" --json`
       - Check if every artifact ID in `applyRequires` has `status: "done"` in the artifacts array
       - Stop when all `applyRequires` artifacts are done

    e. **If an artifact requires user input** (unclear context):
      - Use **AskUserQuestion tool** to clarify
      - Then continue with creation

5. **Show final status**
   ```bash
   openspec status --change "<name>"
   ```

**Output**

After completing all artifacts and reviews, summarize:
- Change name and location
- List of artifacts created with review round counts
- What's ready: "All artifacts created, reviewed, and frozen. Ready for implementation."
- Tell the user: "Say 'apply <name>' when you want me to start implementing the tasks."
- **Do NOT invoke implementation yourself.** Wait for the user to ask.

**Artifact Creation Guidelines**

- Follow the `instruction` field from `openspec instructions` for each artifact type
- The schema defines what each artifact should contain - follow it
- Read dependency artifacts for context before creating new ones
- Use `template` as the structure for your output file - fill in its sections
- **IMPORTANT**: `context` and `rules` are constraints for YOU, not content for the file
  - Do NOT copy `<context>`, `<rules>`, `<project_context>` blocks into the artifact
  - These guide what you write, but should never appear in the output

**Guardrails**
- **tasks.md contains only apply-phase work** — the full rule (what may/may not be a `tasks.md` checkbox, and where change-specific acceptance criteria go) is single-sourced in `openspec/config.yaml` `rules.tasks`, which is prompt-injected into this artifact prompt. Do not restate it here.
- Create ALL artifacts needed for implementation (as defined by schema's `apply.requires`)
- **External-API live probe (design.md):** When design.md introduces new external-API surfaces, run a live probe against the real installed environment before self-review — record the result in design.md. See step 4a for procedure.
- Always read dependency artifacts before creating a new one
- If context is critically unclear, ask the user - but prefer making reasonable decisions to keep momentum
- If a change with that name already exists, ask if user wants to continue it or create a new one
- Verify each artifact file exists after writing before proceeding to next
- **PHASE GATE**: When proposing is complete, STOP. Inform the user and prompt them for the next step. Never invoke the apply/implementation phase without an explicit user request. This is a hard rule.
