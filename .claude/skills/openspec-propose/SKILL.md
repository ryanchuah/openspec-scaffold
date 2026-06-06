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
- design.md (how) → review → freeze
- tasks.md (implementation steps) → review → freeze

**CRITICAL — Do NOT batch-create all artifacts.** Create proposal, review it, fix it, freeze it. Only then create design (using the frozen proposal as context). Repeat for tasks. Downstream artifacts written before upstream ones are frozen will contain stale decisions, requiring extra review rounds to correct. Each unnecessary review round costs real money.

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

   Use the **TodoWrite tool** to track progress through the artifacts.

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
      - Show brief progress: "Created <artifact-id>"

    b. **Self-review the artifact before invoking the reviewer.**
       - Re-read the artifact you just wrote and check it for correctness against the dependencies, template, and context
       - Verify every claim is concrete and implementable, every decision resolves an ambiguity, every scope boundary is explicit
       - Fix any obvious issues you find yourself before calling the reviewer
       - This is the first review pass (out of max 4: 1 self + up to 3 `@openspec-reviewer` passes)

    c. **Invoke `@openspec-reviewer` to audit the artifact.**
       - Use the Task tool with `subagent_type: "openspec-reviewer"` to audit the artifact
       - Append the review output to `review-log.md`
       - If 🔴 blocking issues exist → fix them in the artifact → re-review (max 3 reviewer passes; escalate to user if still unresolved after 3)
       - When a fix is required, make it a **concrete, implementable decision**, not a paraphrase of the problem. E.g., instead of "return value semantics differ" (paraphrase), decide: "returns 0 — zero Document rows inserted" (concrete). If a reviewer flags a gap, close it with a specific choice.
       - If no 🔴 issues → the artifact is frozen; move to the next one
       - **If the reviewer subagent fails for any reason** (model not found, provider error, timeout, etc.): do NOT self-review as a replacement. Halt immediately and escalate to the user with the exact error.
       - **Never skip review or batch-create downstream artifacts.** A design written against an unfrozen proposal will reference stale decisions, causing extra review rounds on every downstream artifact.

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
- Prompt: "Run `/opsx:apply` or ask me to implement to start working on the tasks."

**Artifact Creation Guidelines**

- Follow the `instruction` field from `openspec instructions` for each artifact type
- The schema defines what each artifact should contain - follow it
- Read dependency artifacts for context before creating new ones
- Use `template` as the structure for your output file - fill in its sections
- **IMPORTANT**: `context` and `rules` are constraints for YOU, not content for the file
  - Do NOT copy `<context>`, `<rules>`, `<project_context>` blocks into the artifact
  - These guide what you write, but should never appear in the output

**Guardrails**
- Create ALL artifacts needed for implementation (as defined by schema's `apply.requires`)
- Always read dependency artifacts before creating a new one
- If context is critically unclear, ask the user - but prefer making reasonable decisions to keep momentum
- If a change with that name already exists, ask if user wants to continue it or create a new one
- Verify each artifact file exists after writing before proceeding to next
