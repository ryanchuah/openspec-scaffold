---
name: "OPSX: Sync"
description: Sync delta specs from a change to main specs
category: Workflow
tags: [workflow, sync, experimental]
---

Use the **Skill tool** to invoke `openspec-sync-specs`. The skill file at
`.claude/skills/openspec-sync-specs/SKILL.md` contains the full authoritative
workflow for spec synchronization.

If the user provided a change name, pass it through to the skill context.
