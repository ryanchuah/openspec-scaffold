---
name: openspec-sync-specs
description: Sync delta specs from a change to main specs. Use when the user wants to update main specs with changes from a delta spec, without archiving the change.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Sync delta specs from a change to main specs.

This is a **hybrid** operation: a deterministic script (`scripts/apply_delta_spec.py`) applies the
whole-block, name-keyed operations — **ADDED / REMOVED / RENAMED** — directly to the main specs,
and **you** apply only the **MODIFIED** merges it defers (the one operation that needs judgment —
e.g. adding a scenario without copying the entire requirement). The script never silently
overwrites a canonical spec; it halts and reports on any ambiguous operation.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show changes that have delta specs (under `specs/` directory).

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Resolve change context**

   Run:
   ```bash
   openspec status --change "<name>" --json
   ```

   If status reports `actionContext.mode: "workspace-planning"`, explain that workspace spec sync is not supported in this slice and STOP. Do not fall back to repo-local paths or edit linked repos.

3. **Find delta specs**

   Use `artifactPaths.specs.existingOutputPaths` from the status JSON as the list of delta spec files.

   Each delta spec file contains sections like:
   - `## ADDED Requirements` - New requirements to add
   - `## MODIFIED Requirements` - Changes to existing requirements
   - `## REMOVED Requirements` - Requirements to remove
   - `## RENAMED Requirements` - Requirements to rename (FROM:/TO: format)

   If no delta specs found, inform user and stop.

4. **Promote the delta specs — deterministic ADDED/REMOVED/RENAMED, LLM only for MODIFIED**

   Run the deterministic promoter over the change's delta specs (pass the change root the CLI
   resolved — the parent of the `specs/` dir):

   ```bash
   python3 scripts/apply_delta_spec.py --change-dir "<changeRoot>" --json
   ```

   The promoter applies **ADDED / REMOVED / RENAMED** directly to `openspec/specs/<capability>/spec.md`,
   including **creating a new main spec** (a `## Purpose` TBD + `## Requirements` skeleton, no
   `# <name> Specification` H1) for an ADDED-only delta on a new capability. It writes
   **all-or-nothing** across the change's specs.

   - **Exit `0`** — deterministic operations applied (or nothing to do). The JSON report lists
     `applied` (added/removed/renamed), `skipped` (already-satisfied — e.g. a REMOVED whose target
     was already absent, or an ADDED whose byte-equal block already exists), and `deferred_modified`.
   - **Exit `2`** — an anomaly; the promoter wrote **nothing**. Anomalies are: an ADDED name that
     already exists **with a different body** (the promoter never silently overwrites — a byte-equal
     collision is a skip, a differing one halts); a RENAMED whose FROM/TO are both present or both
     absent; a REMOVED/RENAMED against a nonexistent main spec. **Do not hand-edit around an
     anomaly** — fix the delta or the main spec and re-run.

   Then, **for each requirement in the report's `deferred_modified` list**, apply that MODIFIED
   merge by hand (the one operation that needs judgment):
   - Read the delta's `## MODIFIED Requirements` block for that requirement.
   - Find the matching requirement in `openspec/specs/<capability>/spec.md`.
   - Apply the partial change — add new scenarios (no need to copy existing ones), modify a
     scenario, or change the description — **preserving** scenarios/content the delta does not
     mention.

   ADDED, REMOVED, and RENAMED are already done by the promoter — do not redo them by hand.

5. **Show summary**

   After applying all changes, summarize:
   - Which capabilities were updated
   - What changes were made (requirements added/modified/removed/renamed)

**Delta Spec Format Reference**

```markdown
## ADDED Requirements

### Requirement: New Feature
The system SHALL do something new.

#### Scenario: Basic case
- **WHEN** user does X
- **THEN** system does Y

## MODIFIED Requirements

### Requirement: Existing Feature
#### Scenario: New scenario to add
- **WHEN** user does A
- **THEN** system does B

## REMOVED Requirements

### Requirement: Deprecated Feature

## RENAMED Requirements

- FROM: `### Requirement: Old Name`
- TO: `### Requirement: New Name`
```

**Key Principle: Intelligent Merging (the MODIFIED path only)**

ADDED / REMOVED / RENAMED are applied deterministically by the promoter. For the **MODIFIED**
merges it defers, you apply **partial updates** with judgment:
- To add a scenario, just include that scenario under MODIFIED - don't copy existing scenarios
- The delta represents *intent*, not a wholesale replacement
- Use your judgment to merge changes sensibly

**Output On Success**

```
## Specs Synced: <change-name>

Updated main specs:

**<capability-1>**:
- Added requirement: "New Feature"
- Modified requirement: "Existing Feature" (added 1 scenario)

**<capability-2>**:
- Created new spec file
- Added requirement: "Another Feature"

Main specs are now updated. The change remains active - archive when implementation is complete.
```

**Guardrails**
- ADDED/REMOVED/RENAMED go through `scripts/apply_delta_spec.py` — never hand-apply them; only the
  MODIFIED merges it defers are yours.
- Never hand-edit around a promoter anomaly (exit 2) — fix the delta or the main spec and re-run.
- Read both delta and main specs before making a MODIFIED merge
- Preserve existing content not mentioned in delta
- If something is unclear, ask for clarification
- Show what you're changing as you go
- The operation is idempotent - the promoter reports already-satisfied operations as skips
