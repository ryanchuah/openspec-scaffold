---
name: "OPSX: Bulk Archive"
description: Archive multiple completed changes at once
category: Workflow
tags: [workflow, archive, experimental]
---

Use the **Skill tool** to invoke `openspec-bulk-archive-change`. The skill file at
`.claude/skills/openspec-bulk-archive-change/SKILL.md` contains the full authoritative
workflow with all project-hardened rules (including the mandatory reconciliation step).

If the user provided change names, pass them through to the skill context.
