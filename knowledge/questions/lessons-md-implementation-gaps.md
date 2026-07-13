# lessons.md prescriptions never wired into the live instruction surface

Surfaced by the 2026-07-13 full-repo outstanding-work crawl (`knowledge/lessons.md` cross-checked
against the actual prompt-construction sites for drift between "lesson recorded" and "lesson
applied").

## 1. Openspec-reviewer read-only preamble (primary, higher confidence)

`knowledge/lessons.md` §"Openspec-reviewer bash-crash is NOT a timeout" (around line 111-118)
diagnoses a known crash mode: when the deepseek `openspec-reviewer` agent reaches for `bash`
(denied by permissions) it hard-errors the whole run after ~120s with zero findings, easily
mistaken for a timeout. The lesson prescribes a specific fix — prepend a read-only constraint
preamble to every review prompt (exact wording given in the lesson).

**This was never implemented.** None of the three sites that construct `openspec-reviewer`
prompts carry the preamble:
- `.claude/skills/openspec-propose/SKILL.md` (~line 145-147, base prompt for proposal/design/tasks
  review)
- `.claude/skills/openspec-explore/SKILL.md` (~line 26-32, direction-gate prompt)
- `.claude/skills/openspec-propose/SKILL.md` (~line 213, OpenCode Task-tool path)

The `.opencode/agents/openspec-reviewer.md` agent body also lacks it.

**Why this matters:** the reviewer fires on every propose-phase review round and every explore
direction gate — a live, recurring crash mode with a known, cheap, already-specified fix sitting
unapplied.

**Candidate fix:** SMALL — add the preamble string (already written verbatim in the lesson) to the
three prompt-construction sites plus the agent body. Mechanical, low blast radius, self-contained.

## 2. Git-worktree convention for parallel applies (secondary, weaker evidence)

`knowledge/lessons.md` (~line 93) states "Independent parallel applies MUST use separate git
worktrees" as a lesson, but no skill or AGENTS.md documents `git worktree add` as an actual
mechanized convention — only `knowledge/research/workflow-audit-2026-07-11/AUDIT.md:158` notes a
related "verifier-in-worktree" idea as an explicitly-deferred non-finding.

**Lower confidence this is a genuine gap** — parallel applies are rare in this repo's actual
workflow (apply is deliberately sequential, single-executor, per AGENTS.md "do not fan out
cohesive, dependency-laden work"), so this may be intentional tribal-knowledge advice for a rare
edge case rather than a dropped mechanization. Flagging for operator judgment rather than treating
as an actionable item.
