---
name: "OPSX: Apply"
description: Implement tasks from an OpenSpec change
category: Workflow
tags: [workflow, apply, experimental]
---

Use the **Skill tool** to invoke `openspec-apply-change`. The skill file at
`.claude/skills/openspec-apply-change/SKILL.md` contains the full authoritative
workflow with the mandatory delegation override: the primary agent delegates
implementation to the apply-executor, does not implement inline.

If the user provided a change name (e.g. `/opsx:apply <name>`), pass it through
to the skill context.
