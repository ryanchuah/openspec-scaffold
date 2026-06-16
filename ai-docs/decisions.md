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

## Decision: Per-repo test command for commit-test-gate lives in scripts/test-cmd
**Date:** 2026-06-16
**Decision:** The commit-test-gate script (`scripts/test-gate.sh`, shared/byte-identical across repos) reads the per-repo test command from a one-line file `scripts/test-cmd`. When this file is absent, empty, or whitespace-only, the gate is a no-op (exit 0). When the command's executable cannot be resolved (e.g. fresh clone, missing `.venv`), the gate warns on stderr and allows the commit (exit 0) — it does NOT block on configuration errors that would be hostile to new clones. Only when the command runs and fails does the gate block (exit 2).
**Rationale:** A shared gate script avoids duplicating the test-gating logic across repos. The per-repo file is the single value the forthcoming single-source manifest will carry as a fill; it is intentionally NOT synced/shared. The config-error-as-no-op behavior prevents a missing interpreter from locking all commits in a fresh environment.
**Alternatives considered:** (a) An environment variable — rejected because it cannot be tracked/versioned per repo. (b) A symlink from each repo — rejected as fragile. (c) Blocking on config errors (failing closed) — rejected as hostile to new clones.

## Decision: No lifecycle hooks in the scaffold
**Date:** 2026-06-13
**⚠️ PARTIALLY SUPERSEDED 2026-06-16** — see "Scaffold ships the commit-test-gate hook" below. The general preference still holds (prefer agent/skill guardrails over hooks), but the operator carved out one deliberate exception: the commit-test-gate.
**Decision:** The scaffold ships no harness lifecycle hooks (e.g. Claude Code `settings.json` hooks) — *except the commit-test-gate, per the superseding decision below.*
**Rationale:** Hooks are a Claude-Code-only mechanism with no OpenCode equivalent; relying on them would couple workflow behavior to one harness, violating the cross-agent-compatibility invariant. Equivalent guardrails are enforced in agent definitions and skills, which both harnesses honor.
**Alternatives considered:** Claude Code hooks for guardrails (format/test gates, etc.) — rejected for the template. An instantiated project MAY add Claude-only hooks if it accepts the harness coupling for its own use.

## Decision: Scaffold ships the commit-test-gate hook (carve-out from "No lifecycle hooks")
**Date:** 2026-06-16
**Decision:** The scaffold SHIPS a Claude Code `PreToolUse` hook (in `.claude/settings.json`, on `Bash(git commit*)`) that runs `scripts/test-gate.sh` to block commits whose tests fail. This is a deliberate, operator-approved exception to the "No lifecycle hooks in the scaffold" decision above.
**Rationale:** A deterministic tests-green-before-commit gate is high enough value (it closes the "executor claims tests pass" trust gap at the single chokepoint — the orchestrator's commit) to accept Claude-harness coupling for this one mechanism. The gate degrades safely: it is inert wherever `scripts/test-cmd` is absent (incl. the scaffold itself, which has no tests), so shipping it in the template costs nothing there while making it present for instantiated projects. Part of the `harden-delegation` change.
**Residual / known gap:** enforcement is **Claude-only** for now — OpenCode-driven commits are NOT gated until the deferred OpenCode plugin (v2). The harness-neutral piece (`scripts/test-gate.sh` + the `scripts/test-cmd` convention) is shared; only the wiring is Claude-specific.
**Alternatives considered:** Re-scope so the scaffold ships only the neutral script and instantiated projects wire the hook (honoring the original decision) — considered and rejected by the operator in favor of shipping the hook in the template directly. A git `pre-commit` hook — rejected (`--no-verify` bypass; not a harness control).

## Decision: Executor/reviewer agents are NOT cross-loaded — both `.claude/agents/` and `.opencode/agents/` are required
**Date:** 2026-06-14
**Decision:** The delegated agents live in BOTH directories with different roles and formats — they are NOT consolidated to one copy the way skills are. `.opencode/agents/{apply-executor,archive-executor,openspec-reviewer}.md` (model `deepseek/...`, OpenCode `mode`/`permission` schema) are the PRIMARY executors, invoked via `opencode run --agent <name>` and used by both harnesses. `.claude/agents/{apply-executor,archive-executor}.md` (`model: sonnet`, Claude `tools` schema) are the FALLBACK, invoked via Claude's Task-tool `subagent_type` only when the opencode/deepseek run crashes. There is deliberately NO `.claude/agents/openspec-reviewer.md`: the reviewer must be a different model than the orchestrator, so it is deepseek-only (a Claude reviewer auditing Claude's own work defeats separate-model review).
**Rationale:** Unlike skills, agents do NOT cross-load. opencode 1.17.4 discovers agents from `.opencode/agents/` and `~/.config/opencode/agent` only — the binary carries no `claude/agents/` scan path and no agents opt-out flag (contrast `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`, which exists precisely because skills DO cross-load). The two formats are also not interchangeable (Claude `tools` + `model: sonnet` vs OpenCode `mode`/`permission` + `model: deepseek`), and the two roles select different models on purpose. So a single shared copy is impossible. Removing `.opencode/agents/` would break the deepseek primary path under BOTH harnesses (Claude's primary apply/archive/review shells out to `opencode run --agent`); removing `.claude/agents/` would remove the Sonnet resilience fallback for when opencode/deepseek itself is down. Verified 2026-06-14 against opencode 1.17.4 (binary scan-path inspection) and the agent files' frontmatter.
**Alternatives considered:** (a) Consolidate to one copy under `.claude/agents/` like skills — rejected: OpenCode cannot see `.claude/agents/`, and the formats/models differ. (b) Drop `.claude/agents/` and rely only on opencode — rejected: removes the fallback that exists for `opencode run` failures (the exact operational-crash case the apply/archive skills' failure ladders handle). See the companion "Workflow skills live only under `.claude/skills/`" decision above for the contrasting skills case.

## Decision: Change tiers are STANDING (in AGENTS.md); fast-track governs autonomy only
**Date:** 2026-06-14
**Decision:** The SMALL/MEDIUM/COMPLEX change-tier classification is a standing part of the normal workflow, documented in AGENTS.md `## Change tiers` (every change is classified; the operator initiates tier-2/tier-3 lifecycles). `ai-docs/fast-track-workflow.md` is slimmed to govern ONLY the autonomy override (proceeding without per-step checkpoints), which remains opt-in and trust-gated — dormant unless the operator explicitly grants it.
**Rationale:** Previously the tier definitions lived only inside the (opt-in) fast-track doc, so without a fast-track grant every non-trivial change ran the full lifecycle. Tiering (process-weight scaling) and autonomy (interaction cadence) are independent concerns: tiering should always apply (extrends's proven practice), while autonomy stays opt-in. Separating them lets agents right-size process by default while keeping the conservative phase-gated interaction default. This also harmonizes the golden source with extrends + psc-monitor so all three share these workflow sections.
**Alternatives considered:** Keeping tiers opt-in (bundled inside fast-track) — rejected: it forced full-lifecycle ceremony on small changes absent a grant, and diverged from extrends. Making autonomy standing too — rejected: autonomy stays opt-in per the operator's standing preference (Option A — no active grant in any repo).
