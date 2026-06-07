---
name: "OPSX: Archive"
description: Archive a completed change in the experimental workflow
category: Workflow
tags: [workflow, archive, experimental]
---

Use the **Skill tool** to invoke `openspec-archive-change`. The skill file at
`.claude/skills/openspec-archive-change/SKILL.md` contains the full authoritative
workflow with all project-hardened rules (including the mandatory reconciliation step).

If the user provided a change name (e.g. `/opsx:archive <name>`), pass it through
to the skill context.
