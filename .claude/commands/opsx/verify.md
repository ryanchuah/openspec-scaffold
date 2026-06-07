---
name: "OPSX: Verify"
description: Verify implementation matches change artifacts
category: Workflow
tags: [workflow, verify, experimental]
---

Use the **Skill tool** to invoke `openspec-verify-change`. The skill file at
`.claude/skills/openspec-verify-change/SKILL.md` contains the full authoritative
workflow with all project-hardened rules: mandatory behavioral review preamble
(read diffs, re-run suite, eyeball output, live smoke, re-delegate),
checkpoint-to-notes (step 9), and verbal acknowledgement (step 10).

If the user provided a change name (e.g. `/opsx:verify <name>`), pass it through
to the skill context.
