---
name: "OPSX: Propose"
description: Propose a new change with artifacts generated sequentially and reviewed
category: Workflow
tags: [workflow, propose, experimental]
---

Use the **Skill tool** to invoke `openspec-propose`. The skill file at
`.claude/skills/openspec-propose/SKILL.md` contains the full authoritative
workflow with all project-hardened rules: sequential artifact creation,
rigorous self-review, concrete-fix guidance.

If the user provided a change name, pass it through to the skill context.
