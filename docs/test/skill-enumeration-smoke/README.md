# Skill-Enumeration Smoke

This directory contains a repeatable smoke procedure for verifying that `opencode`
(≥1.16) correctly auto-discovers the `openspec-*` skills from `.claude/skills/`.

The dual-harness design (Claude Code + OpenCode) rests on opencode's ability to
read `.claude/skills/**/SKILL.md` files. This is gated by the environment variable
`OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` — when unset (the default), opencode
automatically loads these skill definitions. See `ai-docs/decisions.md` for the
decision record. An opencode upgrade could silently stop cross-loading skills (the
whole skill layer would vanish for the OpenCode harness, with zero signal) — this
smoke is the check that catches that regression.

## Procedure

Confirm that `opencode debug skill` enumerates all seven `openspec-*` skills. Run
from the scaffold root.

> **Gotcha — capture to a file first, do NOT pipe `opencode debug skill` directly
> into `grep`.** The command emits a very large blob (it dumps the full *content* of
> every SKILL.md, ~120 KB). Piping it straight into `grep | sort` races the stream and
> intermittently returns only a *subset* of the skills (observed: 3–4 of 7 on repeated
> direct-pipe runs). Redirect the full output to a file, then grep the file — that is
> deterministic.

```bash
opencode debug skill > /tmp/skill-dump.txt 2>&1
# distinct openspec skill name fields:
grep -oE '"name": "openspec-[a-z-]+"' /tmp/skill-dump.txt | sort -u
# confirm each is loaded FROM .claude/skills/ (cross-load, not a second copy):
grep -oE '"location": "[^"]*\.claude/skills/openspec-[^"]*"' /tmp/skill-dump.txt | sort -u | wc -l   # expect 7
# confirm the cross-load flag is not disabling it:
echo "OPENCODE_DISABLE_CLAUDE_CODE_SKILLS='${OPENCODE_DISABLE_CLAUDE_CODE_SKILLS:-<unset>}'"          # expect <unset>
```

**Expected output (name list):**

```
"name": "openspec-apply-change"
"name": "openspec-archive-change"
"name": "openspec-explore"
"name": "openspec-onboard"
"name": "openspec-propose"
"name": "openspec-sync-specs"
"name": "openspec-verify-change"
```

If any of the seven is missing, the cross-load wiring is broken — the most likely
cause is `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` being set (check the environment)
or a structural issue in the skill's `SKILL.md` frontmatter.

## Recorded Evidence

**Live run 2026-06-17 against opencode 1.17.7 (`/home/pang/.opencode/bin/opencode`),
from the scaffold root: PASS.**

- All **7** `openspec-*` skills enumerated, names exactly as the expected list above
  (apply-change, archive-change, explore, onboard, propose, sync-specs, verify-change).
- All **7** `"location"` fields resolved to
  `…/openspec-scaffold/.claude/skills/openspec-*/SKILL.md` — confirming opencode
  cross-loads them from `.claude/skills/` (there is no second `.opencode/skills/` copy).
- `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` was `<unset>` — the cross-load path is active by default.
- Closes the W0 carry-forward / audit-E5 item (see `ai-docs/decisions.md`
  "opencode skill-enumeration smoke" and the resolved entry in `ai-docs/open-questions.md`).
- The ~119 KB file capture is the authoritative method; the direct-pipe form flaked to a
  3–4 skill subset before file-capture was adopted (see Gotcha).
