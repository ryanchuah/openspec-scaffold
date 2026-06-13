# Decisions

Durable architectural decisions and their rationale. Add an entry whenever a non-obvious choice is made that a future agent would otherwise re-litigate.

---

<!-- Format:
## Decision: <short title>
**Date:** YYYY-MM-DD
**Decision:** What was decided.
**Rationale:** Why.
**Alternatives considered:** What was rejected and why.
-->

## Decision: All project state in tracked, agent-neutral files — no harness-native memory
**Date:** 2026-06-13
**Decision:** Project state lives only in tracked files (`AGENTS.md`, `ai-docs/`, `openspec/`). Agents must not rely on harness-native memory (Claude memory, OpenCode session memory, etc.) to carry project state across turns or sessions.
**Rationale:** This repo is worked by both Claude Code and OpenCode/DeepSeek agents; only tracked files are visible to both. A harness-native store would be invisible to the other harness and silently break cross-agent continuity.
**Alternatives considered:** Anthropic's native memory tool (reported ~39% agentic-search gain / ~84% token reduction in its Sept-2025 benchmark — figures per Anthropic, not independently verified) was rejected: it is Claude-only with no OpenCode equivalent, so it cannot be the shared state store for a dual-harness workflow. Revisit only if the dual-harness requirement is ever dropped.

## Decision: Workflow skills live only under `.claude/skills/` — not duplicated to `.opencode/`
**Date:** 2026-06-13
**Decision:** The OpenSpec workflow skills are kept as a single copy under `.claude/skills/openspec-*/SKILL.md`; they are NOT duplicated into an `.opencode/skills/` directory.
**Rationale:** OpenCode ≥ 1.16 auto-discovers `.claude/skills/**/SKILL.md` (gated by the env var `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`, default false), so both harnesses load the same skill files from one location. A second copy would create a divergence hazard (two sources drifting apart). Verified 2026-06-13 against opencode 1.17.4: the installed binary carries the `claude/skills/` scan path and the disable flag is unset.
**Alternatives considered:** A second `.opencode/skills/` copy, or a symlink `.opencode/skills/` → `.claude/skills/` — both rejected as redundant given the auto cross-load, and as a maintenance/divergence risk.

## Decision: No lifecycle hooks in the scaffold
**Date:** 2026-06-13
**Decision:** The scaffold ships no harness lifecycle hooks (e.g. Claude Code `settings.json` hooks).
**Rationale:** Hooks are a Claude-Code-only mechanism with no OpenCode equivalent; relying on them would couple workflow behavior to one harness, violating the cross-agent-compatibility invariant. Equivalent guardrails are enforced in agent definitions and skills, which both harnesses honor.
**Alternatives considered:** Claude Code hooks for guardrails (format/test gates, etc.) — rejected for the template. An instantiated project MAY add Claude-only hooks if it accepts the harness coupling for its own use.
